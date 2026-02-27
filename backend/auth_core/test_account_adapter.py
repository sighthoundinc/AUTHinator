"""
Tests for auth_core account adapters.

Testing custom account and social account adapters for SSO.
Target: 100% coverage
"""
import pytest
from django.test import RequestFactory
from unittest.mock import Mock, MagicMock
from auth_core.account_adapter import CustomAccountAdapter, CustomSocialAccountAdapter
from users.models import User


@pytest.mark.django_db
class TestCustomAccountAdapter:
    """Test suite for CustomAccountAdapter."""
    
    def test_is_open_for_signup_returns_true(self):
        """Test that signup is open for SSO users."""
        adapter = CustomAccountAdapter()
        request = RequestFactory().get('/')
        
        result = adapter.is_open_for_signup(request)
        
        assert result is True


@pytest.mark.django_db
class TestCustomSocialAccountAdapter:
    """Test suite for CustomSocialAccountAdapter."""
    
    def test_is_auto_signup_allowed_returns_true(self):
        """Test that auto-signup is allowed for SSO providers."""
        adapter = CustomSocialAccountAdapter()
        request = RequestFactory().get('/')
        sociallogin = Mock()
        
        result = adapter.is_auto_signup_allowed(request, sociallogin)
        
        assert result is True
    
    def test_populate_user_sets_email_from_data(self):
        """Test that populate_user sets email from social account data."""
        adapter = CustomSocialAccountAdapter()
        request = RequestFactory().get('/')
        
        # Create a mock sociallogin
        sociallogin = Mock()
        
        # Create data with email
        data = {
            'email': 'test@example.com',
            'username': 'testuser'
        }
        
        # Mock the parent populate_user to return a user without email
        user = User(username='testuser')
        adapter.__class__.__bases__[0].populate_user = Mock(return_value=user)
        
        result = adapter.populate_user(request, sociallogin, data)
        
        assert result.email == 'test@example.com'
        assert result.is_verified is True
    
    def test_populate_user_sets_verified_flag(self):
        """Test that populate_user marks user as verified."""
        adapter = CustomSocialAccountAdapter()
        request = RequestFactory().get('/')
        sociallogin = Mock()
        data = {'username': 'testuser', 'email': 'test@example.com'}
        
        # Mock the parent populate_user
        user = User(username='testuser', email='test@example.com')
        adapter.__class__.__bases__[0].populate_user = Mock(return_value=user)
        
        result = adapter.populate_user(request, sociallogin, data)
        
        assert result.is_verified is True
    
    def test_populate_user_preserves_existing_email(self):
        """Test that populate_user doesn't override existing email."""
        adapter = CustomSocialAccountAdapter()
        request = RequestFactory().get('/')
        sociallogin = Mock()
        data = {'username': 'testuser', 'email': 'newemail@example.com'}
        
        # Mock the parent populate_user to return user with existing email
        user = User(username='testuser', email='existing@example.com')
        adapter.__class__.__bases__[0].populate_user = Mock(return_value=user)
        
        result = adapter.populate_user(request, sociallogin, data)
        
        # Should keep the email set by parent
        assert result.email == 'existing@example.com'
        assert result.is_verified is True
    
    def test_populate_user_without_email_in_data(self):
        """Test that populate_user handles missing email in data."""
        adapter = CustomSocialAccountAdapter()
        request = RequestFactory().get('/')
        sociallogin = Mock()
        data = {'username': 'testuser'}
        
        # Mock the parent populate_user
        user = User(username='testuser')
        adapter.__class__.__bases__[0].populate_user = Mock(return_value=user)
        
        result = adapter.populate_user(request, sociallogin, data)
        
        assert result.email == ''
        assert result.is_verified is True
