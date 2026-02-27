"""
MFA views for AUTHinator.

Provides endpoints for:
- TOTP (Time-based One-Time Password) setup, confirmation, and disabling
- WebAuthn credential registration, listing, and deletion
- MFA login verification (TOTP and WebAuthn as second factor during login)
"""
import base64
import io
import json

import pyotp
import qrcode
import webauthn
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from django.conf import settings
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import WebAuthnCredential
from users.models import User


# WebAuthn Relying Party configuration
RP_ID = getattr(settings, 'WEBAUTHN_RP_ID', 'localhost')
RP_NAME = getattr(settings, 'WEBAUTHN_RP_NAME', 'AUTHinator')
WEBAUTHN_ORIGIN = getattr(settings, 'WEBAUTHN_ORIGIN', 'http://localhost:3001')

# MFA token signer (must match the one in auth_core.views)
MFA_TOKEN_MAX_AGE = 300  # 5 minutes
mfa_signer = TimestampSigner(salt='mfa-login')


def _verify_mfa_token(mfa_token):
    """
    Verify an MFA token and return the associated user.

    Returns (user, None) on success or (None, error_response) on failure.
    """
    try:
        user_id = mfa_signer.unsign(mfa_token, max_age=MFA_TOKEN_MAX_AGE)
    except SignatureExpired:
        return None, Response(
            {'error': 'MFA token has expired. Please log in again.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except BadSignature:
        return None, Response(
            {'error': 'Invalid MFA token'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(id=int(user_id))
    except User.DoesNotExist:
        return None, Response(
            {'error': 'Invalid MFA token'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return user, None


def _issue_jwt_tokens(user):
    """Generate JWT access + refresh tokens for the given user."""
    refresh = RefreshToken.for_user(user)
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    })


# ─── TOTP Endpoints ───────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def totp_status(request):
    """Return whether TOTP is enabled for the current user."""
    return Response({'enabled': request.user.totp_enabled})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def totp_setup(request):
    """
    Generate a new TOTP secret and QR code.

    The secret is stored on the user but TOTP is not yet enabled —
    the user must confirm with a valid token via /totp/confirm/.
    """
    user = request.user

    # Generate a new secret
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.save(update_fields=['totp_secret'])

    # Build provisioning URI for authenticator apps
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(
        name=user.email or user.username,
        issuer_name=RP_NAME,
    )

    # Generate QR code as base64 data URI
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    qr_b64 = base64.b64encode(buf.getvalue()).decode()
    qr_data_uri = f'data:image/png;base64,{qr_b64}'

    return Response({
        'qr_code': qr_data_uri,
        'secret': secret,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def totp_confirm(request):
    """
    Verify a TOTP token and enable 2FA.

    Request body: { "token": "123456" }
    """
    user = request.user
    token = request.data.get('token', '')

    if not user.totp_secret:
        return Response(
            {'error': 'TOTP has not been set up. Call /totp/setup/ first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(token):
        return Response(
            {'error': 'Invalid verification code'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.totp_enabled = True
    user.save(update_fields=['totp_enabled'])
    return Response({'detail': 'TOTP enabled successfully'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def totp_disable(request):
    """
    Disable TOTP after verifying the current token.

    Request body: { "token": "123456" }
    """
    user = request.user
    token = request.data.get('token', '')

    if not user.totp_enabled or not user.totp_secret:
        return Response(
            {'error': 'TOTP is not currently enabled'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(token):
        return Response(
            {'error': 'Invalid verification code'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.totp_secret = None
    user.totp_enabled = False
    user.save(update_fields=['totp_secret', 'totp_enabled'])
    return Response({'detail': 'TOTP disabled successfully'})


# ─── WebAuthn Endpoints ───────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def webauthn_credentials(request):
    """List all WebAuthn credentials for the current user."""
    creds = request.user.webauthn_credentials.all()
    data = [
        {
            'id': c.id,
            'name': c.name,
            'created_at': c.created_at.isoformat(),
        }
        for c in creds
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webauthn_register_begin(request):
    """
    Begin WebAuthn credential registration.

    Returns PublicKeyCredentialCreationOptions for the browser.
    """
    user = request.user
    name = request.data.get('name', 'Security Key')

    # Build list of existing credential IDs to exclude
    existing = user.webauthn_credentials.all()
    exclude_credentials = [
        webauthn.helpers.structs.PublicKeyCredentialDescriptor(
            id=bytes(cred.credential_id),
        )
        for cred in existing
    ]

    options = webauthn.generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=str(user.id).encode(),
        user_name=user.username,
        user_display_name=user.get_full_name() or user.username,
        exclude_credentials=exclude_credentials,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.DISCOURAGED,
            user_verification=UserVerificationRequirement.DISCOURAGED,
        ),
    )

    # Store the challenge and credential name on the user for verification
    user.webauthn_registration_challenge = base64.b64encode(options.challenge).decode()
    user.webauthn_registration_name = name
    user.save(update_fields=['webauthn_registration_challenge', 'webauthn_registration_name'])

    # Serialize options to JSON-compatible dict
    options_json = webauthn.options_to_json(options)

    return Response({'options': json.loads(options_json)})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def webauthn_register_complete(request):
    """
    Complete WebAuthn credential registration.

    The request body is the credential response from the browser.
    """
    user = request.user
    challenge_b64 = user.webauthn_registration_challenge
    credential_name = user.webauthn_registration_name or 'Security Key'

    if not challenge_b64:
        return Response(
            {'error': 'No registration in progress'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    challenge = base64.b64decode(challenge_b64)

    try:
        credential = webauthn.verify_registration_response(
            credential=request.data,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
        )
    except Exception as e:
        return Response(
            {'error': f'Registration verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Store the credential
    WebAuthnCredential.objects.create(
        user=user,
        name=credential_name,
        credential_id=credential.credential_id,
        public_key=credential.credential_public_key,
        sign_count=credential.sign_count,
    )

    # Clean up registration state
    user.webauthn_registration_challenge = None
    user.webauthn_registration_name = None
    user.save(update_fields=['webauthn_registration_challenge', 'webauthn_registration_name'])

    return Response({'detail': 'Security key registered successfully'})


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def webauthn_credential_delete(request, credential_id):
    """Delete a WebAuthn credential by ID (must belong to the current user)."""
    try:
        cred = WebAuthnCredential.objects.get(
            id=credential_id,
            user=request.user,
        )
    except WebAuthnCredential.DoesNotExist:
        return Response(
            {'error': 'Credential not found'},
            status=status.HTTP_404_NOT_FOUND,
        )

    cred.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


# ─── MFA Login Verification Endpoints ─────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_totp_verify(request):
    """
    Verify TOTP code during login and issue JWT tokens.

    Request body: { "mfa_token": "...", "code": "123456" }
    """
    mfa_token = request.data.get('mfa_token', '')
    code = request.data.get('code', '')

    if not mfa_token or not code:
        return Response(
            {'error': 'mfa_token and code are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user, err = _verify_mfa_token(mfa_token)
    if err:
        return err

    if not user.totp_enabled or not user.totp_secret:
        return Response(
            {'error': 'TOTP is not enabled for this account'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(code):
        return Response(
            {'error': 'Invalid verification code'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return _issue_jwt_tokens(user)


@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_webauthn_begin(request):
    """
    Begin WebAuthn authentication during login.

    Returns PublicKeyCredentialRequestOptions for the browser.
    Request body: { "mfa_token": "..." }
    """
    mfa_token = request.data.get('mfa_token', '')

    if not mfa_token:
        return Response(
            {'error': 'mfa_token is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user, err = _verify_mfa_token(mfa_token)
    if err:
        return err

    credentials = user.webauthn_credentials.all()
    if not credentials.exists():
        return Response(
            {'error': 'No security keys registered for this account'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    allow_credentials = [
        webauthn.helpers.structs.PublicKeyCredentialDescriptor(
            id=bytes(cred.credential_id),
        )
        for cred in credentials
    ]

    options = webauthn.generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.DISCOURAGED,
    )

    # Store challenge on user model for verification
    user.webauthn_auth_challenge = base64.b64encode(options.challenge).decode()
    user.save(update_fields=['webauthn_auth_challenge'])

    options_json = webauthn.options_to_json(options)
    return Response({'options': json.loads(options_json)})


@api_view(['POST'])
@permission_classes([AllowAny])
def mfa_webauthn_complete(request):
    """
    Complete WebAuthn authentication during login and issue JWT tokens.

    Request body: { "mfa_token": "...", ...assertion }
    """
    mfa_token = request.data.get('mfa_token', '')

    if not mfa_token:
        return Response(
            {'error': 'mfa_token is required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user, err = _verify_mfa_token(mfa_token)
    if err:
        return err

    challenge_b64 = user.webauthn_auth_challenge
    if not challenge_b64:
        return Response(
            {'error': 'No authentication in progress'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    challenge = base64.b64decode(challenge_b64)

    # Find the matching credential
    credential_id_b64 = request.data.get('rawId', request.data.get('id', ''))
    if isinstance(credential_id_b64, str):
        # URL-safe base64 decode
        padding = 4 - len(credential_id_b64) % 4
        if padding != 4:
            credential_id_b64 += '=' * padding
        try:
            credential_id_bytes = base64.urlsafe_b64decode(credential_id_b64)
        except Exception:
            credential_id_bytes = b''
    else:
        credential_id_bytes = b''

    matching_cred = None
    for cred in user.webauthn_credentials.all():
        if bytes(cred.credential_id) == credential_id_bytes:
            matching_cred = cred
            break

    if not matching_cred:
        return Response(
            {'error': 'Credential not recognized'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        verification = webauthn.verify_authentication_response(
            credential=request.data,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=WEBAUTHN_ORIGIN,
            credential_public_key=bytes(matching_cred.public_key),
            credential_current_sign_count=matching_cred.sign_count,
        )
    except Exception as e:
        return Response(
            {'error': f'Authentication verification failed: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Update sign count
    matching_cred.sign_count = verification.new_sign_count
    matching_cred.save(update_fields=['sign_count'])

    # Clean up
    user.webauthn_auth_challenge = None
    user.save(update_fields=['webauthn_auth_challenge'])

    return _issue_jwt_tokens(user)
