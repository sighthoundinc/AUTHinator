"""
Tests for auth_core signal handlers.

Testing SSO authentication signal handlers.
Target: 100% coverage
"""
import pytest
from django.test import RequestFactory
from unittest.mock import Mock, patch
from allauth.socialaccount.models import SocialAccount, SocialLogin
from auth_core.signals import handle_social_login
from users.models import User, Customer


@pytest.mark.django_db
class TestHandleSocialLogin:
    """Test suite for handle_social_login signal handler."""
    
    @pytest.fixture
    def request_obj(self):
        """Create a test request."""
        return RequestFactory().get('/')
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(name='Test Customer')
    
    def test_existing_social_login_returns_early(self, request_obj):
        """Test that existing social logins are skipped."""
        # Create a mock sociallogin that is already existing
        sociallogin = Mock()
        sociallogin.is_existing = True
        
        # Should return early without doing anything
        result = handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        assert result is None
    
    def test_connects_to_existing_user_with_matching_email(self, request_obj, customer):
        """Test that social login connects to existing user with same email."""
        # Create an existing user
        user = User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123',
            customer=customer
        )
        
        # Create a mock sociallogin with matching email
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {'email': 'test@example.com'}
        
        # Call the handler
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        # Verify connect was called with the existing user
        sociallogin.connect.assert_called_once_with(request_obj, user)
    
    def test_no_connect_when_user_does_not_exist(self, request_obj):
        """Test that no connection is made when user doesn't exist."""
        # Create a mock sociallogin with non-existing email
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {'email': 'nonexistent@example.com'}
        
        # Call the handler - should not raise exception
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        # Connect should not be called
        sociallogin.connect.assert_not_called()
    
    def test_handles_missing_email_field(self, request_obj):
        """Test that handler works when email is not in extra_data."""
        # Create a mock sociallogin without email
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {'username': 'testuser'}
        
        # Should not raise exception
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        sociallogin.connect.assert_not_called()
    
    def test_uses_mail_field_as_fallback(self, request_obj, customer):
        """Test that 'mail' field is used as fallback for email."""
        # Create an existing user
        user = User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123',
            customer=customer
        )
        
        # Create a mock sociallogin with 'mail' instead of 'email'
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {'mail': 'test@example.com'}
        
        # Call the handler
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        # Verify connect was called
        sociallogin.connect.assert_called_once_with(request_obj, user)
    
    def test_uses_user_principal_name_as_fallback(self, request_obj, customer):
        """Test that 'userPrincipalName' field is used as fallback for email."""
        # Create an existing user
        user = User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='testpass123',
            customer=customer
        )
        
        # Create a mock sociallogin with 'userPrincipalName'
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {'userPrincipalName': 'test@example.com'}
        
        # Call the handler
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        # Verify connect was called
        sociallogin.connect.assert_called_once_with(request_obj, user)
    
    def test_email_field_takes_precedence(self, request_obj, customer):
        """Test that 'email' field takes precedence over fallbacks."""
        # Create an existing user
        user = User.objects.create_user(
            username='existinguser',
            email='primary@example.com',
            password='testpass123',
            customer=customer
        )
        
        # Create another user with different email
        User.objects.create_user(
            username='otheruser',
            email='secondary@example.com',
            password='testpass123',
            customer=customer
        )
        
        # Create a mock sociallogin with multiple email fields
        sociallogin = Mock()
        sociallogin.is_existing = False
        sociallogin.account = Mock()
        sociallogin.account.extra_data = {
            'email': 'primary@example.com',
            'mail': 'secondary@example.com',
            'userPrincipalName': 'tertiary@example.com'
        }
        
        # Call the handler
        handle_social_login(
            sender=None,
            request=request_obj,
            sociallogin=sociallogin
        )
        
        # Should connect to the user with primary email
        sociallogin.connect.assert_called_once_with(request_obj, user)
