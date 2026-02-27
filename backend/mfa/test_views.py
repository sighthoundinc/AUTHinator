"""
Tests for MFA views (TOTP and WebAuthn).

Following Deft TDD: Target ≥85% coverage.
"""
import pytest
import pyotp
from unittest.mock import patch, MagicMock
from django.test import Client
from users.models import User, Customer
from mfa.models import WebAuthnCredential


@pytest.fixture
def customer(db):
    return Customer.objects.create(name='Test Corp', contact_email='corp@test.com')


@pytest.fixture
def user(customer):
    u = User.objects.create_user(
        username='testuser',
        password='testpass123',
        email='test@test.com',
        customer=customer,
        is_verified=True,
    )
    return u


@pytest.fixture
def auth_client(user):
    """Client authenticated via JWT."""
    client = Client()
    response = client.post(
        '/api/auth/login/',
        {'username': 'testuser', 'password': 'testpass123'},
        content_type='application/json',
    )
    token = response.json()['access']
    client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {token}'
    return client


# ─── TOTP Tests ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTotpStatus:
    def test_returns_false_when_not_enabled(self, auth_client):
        response = auth_client.get('/api/auth/totp/status/')
        assert response.status_code == 200
        assert response.json()['enabled'] is False

    def test_returns_true_when_enabled(self, auth_client, user):
        user.totp_secret = pyotp.random_base32()
        user.totp_enabled = True
        user.save()
        response = auth_client.get('/api/auth/totp/status/')
        assert response.status_code == 200
        assert response.json()['enabled'] is True

    def test_requires_authentication(self):
        client = Client()
        response = client.get('/api/auth/totp/status/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestTotpSetup:
    def test_generates_qr_code_and_secret(self, auth_client, user):
        response = auth_client.post('/api/auth/totp/setup/')
        assert response.status_code == 200
        data = response.json()
        assert 'qr_code' in data
        assert data['qr_code'].startswith('data:image/png;base64,')
        assert 'secret' in data
        assert len(data['secret']) == 32  # base32 encoded

        # Verify secret was stored on user
        user.refresh_from_db()
        assert user.totp_secret == data['secret']
        assert user.totp_enabled is False  # not yet confirmed

    def test_requires_authentication(self):
        client = Client()
        response = client.post('/api/auth/totp/setup/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestTotpConfirm:
    def test_enables_totp_with_valid_token(self, auth_client, user):
        # Setup first
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()

        # Generate a valid token
        totp = pyotp.TOTP(secret)
        token = totp.now()

        response = auth_client.post(
            '/api/auth/totp/confirm/',
            {'token': token},
            content_type='application/json',
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.totp_enabled is True

    def test_rejects_invalid_token(self, auth_client, user):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.save()

        response = auth_client.post(
            '/api/auth/totp/confirm/',
            {'token': '000000'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'error' in response.json()

    def test_fails_without_prior_setup(self, auth_client):
        response = auth_client.post(
            '/api/auth/totp/confirm/',
            {'token': '123456'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'setup' in response.json()['error'].lower()


@pytest.mark.django_db
class TestTotpDisable:
    def test_disables_totp_with_valid_token(self, auth_client, user):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.totp_enabled = True
        user.save()

        totp = pyotp.TOTP(secret)
        token = totp.now()

        response = auth_client.post(
            '/api/auth/totp/disable/',
            {'token': token},
            content_type='application/json',
        )
        assert response.status_code == 200

        user.refresh_from_db()
        assert user.totp_enabled is False
        assert user.totp_secret is None

    def test_rejects_invalid_token(self, auth_client, user):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.totp_enabled = True
        user.save()

        response = auth_client.post(
            '/api/auth/totp/disable/',
            {'token': '000000'},
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_fails_when_not_enabled(self, auth_client):
        response = auth_client.post(
            '/api/auth/totp/disable/',
            {'token': '123456'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'not currently enabled' in response.json()['error'].lower()


# ─── MFA Login Verification Tests ─────────────────────────────────────────────

@pytest.mark.django_db
class TestMfaTotpVerify:
    """Tests for POST /api/auth/mfa/totp-verify/."""

    def _get_mfa_token(self, client, username='testuser', password='testpass123'):
        response = client.post(
            '/api/auth/login/',
            {'username': username, 'password': password},
            content_type='application/json',
        )
        return response.json().get('mfa_token')

    def test_returns_jwt_tokens_with_valid_code(self, user):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.totp_enabled = True
        user.save()

        client = Client()
        mfa_token = self._get_mfa_token(client)
        assert mfa_token is not None

        totp = pyotp.TOTP(secret)
        response = client.post(
            '/api/auth/mfa/totp-verify/',
            {'mfa_token': mfa_token, 'code': totp.now()},
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data

    def test_rejects_invalid_code(self, user):
        secret = pyotp.random_base32()
        user.totp_secret = secret
        user.totp_enabled = True
        user.save()

        client = Client()
        mfa_token = self._get_mfa_token(client)

        response = client.post(
            '/api/auth/mfa/totp-verify/',
            {'mfa_token': mfa_token, 'code': '000000'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'Invalid' in response.json()['error']

    def test_rejects_invalid_mfa_token(self):
        client = Client()
        response = client.post(
            '/api/auth/mfa/totp-verify/',
            {'mfa_token': 'bogus', 'code': '123456'},
            content_type='application/json',
        )
        assert response.status_code == 400

    def test_rejects_missing_fields(self):
        client = Client()
        response = client.post(
            '/api/auth/mfa/totp-verify/',
            {},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'required' in response.json()['error'].lower()

    def test_rejects_when_totp_not_enabled(self, user):
        """Edge case: user somehow has mfa_token but TOTP got disabled."""
        user.totp_secret = pyotp.random_base32()
        user.totp_enabled = True
        user.save()

        client = Client()
        mfa_token = self._get_mfa_token(client)

        # Disable TOTP after getting MFA token
        user.totp_enabled = False
        user.totp_secret = None
        user.save()

        response = client.post(
            '/api/auth/mfa/totp-verify/',
            {'mfa_token': mfa_token, 'code': '123456'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'not enabled' in response.json()['error'].lower()


@pytest.mark.django_db
class TestMfaWebauthnBegin:
    """Tests for POST /api/auth/mfa/webauthn-begin/."""

    def _get_mfa_token(self, client, username='testuser', password='testpass123'):
        response = client.post(
            '/api/auth/login/',
            {'username': username, 'password': password},
            content_type='application/json',
        )
        return response.json().get('mfa_token')

    @patch('mfa.views.webauthn.generate_authentication_options')
    @patch('mfa.views.webauthn.options_to_json')
    def test_returns_authentication_options(self, mock_to_json, mock_gen, user):
        WebAuthnCredential.objects.create(
            user=user, name='Key',
            credential_id=b'\x01\x02\x03',
            public_key=b'\x04\x05\x06',
        )

        mock_options = MagicMock()
        mock_options.challenge = b'\x00' * 32
        mock_gen.return_value = mock_options
        mock_to_json.return_value = '{"challenge": "AAAA"}'

        client = Client()
        mfa_token = self._get_mfa_token(client)
        assert mfa_token is not None

        response = client.post(
            '/api/auth/mfa/webauthn-begin/',
            {'mfa_token': mfa_token},
            content_type='application/json',
        )
        assert response.status_code == 200
        assert 'options' in response.json()
        mock_gen.assert_called_once()

        # Verify challenge stored on user model
        user.refresh_from_db()
        assert user.webauthn_auth_challenge is not None

    def test_rejects_user_without_credentials(self, user):
        user.totp_secret = pyotp.random_base32()
        user.totp_enabled = True
        user.save()

        client = Client()
        mfa_token = self._get_mfa_token(client)

        response = client.post(
            '/api/auth/mfa/webauthn-begin/',
            {'mfa_token': mfa_token},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'No security keys' in response.json()['error']

    def test_rejects_missing_mfa_token(self):
        client = Client()
        response = client.post(
            '/api/auth/mfa/webauthn-begin/',
            {},
            content_type='application/json',
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestMfaWebauthnComplete:
    """Tests for POST /api/auth/mfa/webauthn-complete/."""

    def test_rejects_without_active_challenge(self, user):
        from django.core.signing import TimestampSigner
        signer = TimestampSigner(salt='mfa-login')
        mfa_token = signer.sign(str(user.id))

        client = Client()
        response = client.post(
            '/api/auth/mfa/webauthn-complete/',
            {'mfa_token': mfa_token, 'id': 'test'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'No authentication in progress' in response.json()['error']

    def test_rejects_missing_mfa_token(self):
        client = Client()
        response = client.post(
            '/api/auth/mfa/webauthn-complete/',
            {'id': 'test'},
            content_type='application/json',
        )
        assert response.status_code == 400


# ─── WebAuthn Tests ───────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWebauthnCredentials:
    def test_returns_empty_list(self, auth_client):
        response = auth_client.get('/api/auth/webauthn/credentials/')
        assert response.status_code == 200
        assert response.json() == []

    def test_returns_credentials(self, auth_client, user):
        WebAuthnCredential.objects.create(
            user=user,
            name='YubiKey',
            credential_id=b'\x01\x02\x03',
            public_key=b'\x04\x05\x06',
            sign_count=0,
        )
        response = auth_client.get('/api/auth/webauthn/credentials/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'YubiKey'
        assert 'created_at' in data[0]

    def test_requires_authentication(self):
        client = Client()
        response = client.get('/api/auth/webauthn/credentials/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestWebauthnRegisterBegin:
    @patch('mfa.views.webauthn.generate_registration_options')
    @patch('mfa.views.webauthn.options_to_json')
    def test_returns_registration_options(self, mock_to_json, mock_gen, auth_client, user):
        mock_options = MagicMock()
        mock_options.challenge = b'\x00' * 32
        mock_gen.return_value = mock_options
        mock_to_json.return_value = '{"challenge": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="}'

        response = auth_client.post(
            '/api/auth/webauthn/register/begin/',
            {'name': 'My Key'},
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert 'options' in data
        mock_gen.assert_called_once()

        # Verify challenge and name stored on user model (not session)
        user.refresh_from_db()
        assert user.webauthn_registration_challenge is not None
        assert user.webauthn_registration_name == 'My Key'


@pytest.mark.django_db
class TestWebauthnRegisterComplete:
    def test_fails_without_active_registration(self, auth_client):
        response = auth_client.post(
            '/api/auth/webauthn/register/complete/',
            {'id': 'test'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'No registration in progress' in response.json()['error']


@pytest.mark.django_db
class TestWebauthnCredentialDelete:
    def test_deletes_own_credential(self, auth_client, user):
        cred = WebAuthnCredential.objects.create(
            user=user,
            name='YubiKey',
            credential_id=b'\x01\x02\x03',
            public_key=b'\x04\x05\x06',
        )
        response = auth_client.delete(f'/api/auth/webauthn/credentials/{cred.id}/')
        assert response.status_code == 204
        assert not WebAuthnCredential.objects.filter(id=cred.id).exists()

    def test_cannot_delete_other_users_credential(self, auth_client, customer):
        other = User.objects.create_user(
            username='other', password='pass', customer=customer, is_verified=True,
        )
        cred = WebAuthnCredential.objects.create(
            user=other,
            name='Other Key',
            credential_id=b'\x01',
            public_key=b'\x02',
        )
        response = auth_client.delete(f'/api/auth/webauthn/credentials/{cred.id}/')
        assert response.status_code == 404

    def test_returns_404_for_nonexistent(self, auth_client):
        response = auth_client.delete('/api/auth/webauthn/credentials/9999/')
        assert response.status_code == 404
