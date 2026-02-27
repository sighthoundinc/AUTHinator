from django.db import models
from django.conf import settings


class WebAuthnCredential(models.Model):
    """
    Stores a WebAuthn (FIDO2) credential for a user.
    Supports hardware security keys and biometric authenticators.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='webauthn_credentials',
    )
    name = models.CharField(
        max_length=255,
        help_text="User-provided name for this credential (e.g. 'YubiKey')"
    )
    credential_id = models.BinaryField(
        help_text="WebAuthn credential ID"
    )
    public_key = models.BinaryField(
        help_text="COSE public key bytes"
    )
    sign_count = models.PositiveIntegerField(
        default=0,
        help_text="Signature counter for clone detection"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'WebAuthn Credential'
        verbose_name_plural = 'WebAuthn Credentials'

    def __str__(self):
        return f"{self.name} ({self.user.username})"
