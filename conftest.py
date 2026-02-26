"""
Pytest configuration for Authinator tests.
"""
import pytest


@pytest.fixture(autouse=True)
def email_backend_setup(settings):
    """Configure email backend for testing."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
