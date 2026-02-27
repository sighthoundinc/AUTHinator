"""
Tests for auth_core SSO adapters.

Testing custom social account adapter for SSO provider configuration.
Target: 100% coverage
"""
import pytest
from django.test import RequestFactory
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from auth_core.adapters import CustomSocialAccountAdapter


@pytest.mark.django_db
class TestCustomSocialAccountAdapter:
    """Test suite for CustomSocialAccountAdapter."""
    
    @pytest.fixture
    def adapter(self):
        """Create an adapter instance."""
        return CustomSocialAccountAdapter()
    
    @pytest.fixture
    def site(self):
        """Create a test site."""
        site, _ = Site.objects.get_or_create(
            id=1,
            defaults={'domain': 'testserver', 'name': 'Test Site'}
        )
        return site
    
    @pytest.fixture
    def request_obj(self, site):
        """Create a mock request with site."""
        request = RequestFactory().get('/')
        request.site = site
        return request
    
    def test_get_app_returns_existing_app(self, adapter, request_obj, site):
        """Test that get_app returns an existing social app."""
        # Create a social app
        app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth',
            client_id='test-client-id',
            secret='test-secret'
        )
        app.sites.add(site)
        
        result = adapter.get_app(request_obj, 'google')
        
        assert result == app
        assert result.provider == 'google'
    
    def test_get_app_with_client_id_filter(self, adapter, request_obj, site):
        """Test that get_app filters by client_id when provided."""
        # Create multiple apps for same provider
        app1 = SocialApp.objects.create(
            provider='google',
            name='Google OAuth 1',
            client_id='client-1',
            secret='secret-1'
        )
        app1.sites.add(site)
        
        app2 = SocialApp.objects.create(
            provider='google',
            name='Google OAuth 2',
            client_id='client-2',
            secret='secret-2'
        )
        app2.sites.add(site)
        
        result = adapter.get_app(request_obj, 'google', client_id='client-2')
        
        assert result == app2
        assert result.client_id == 'client-2'
    
    def test_get_app_raises_does_not_exist_when_no_app(self, adapter, request_obj):
        """Test that get_app raises DoesNotExist when no app found."""
        with pytest.raises(SocialApp.DoesNotExist) as exc_info:
            adapter.get_app(request_obj, 'nonexistent-provider')
        
        assert 'nonexistent-provider' in str(exc_info.value)
    
    def test_get_app_returns_first_when_multiple_apps(self, adapter, request_obj, site):
        """Test that get_app returns first match when multiple apps exist."""
        # Create multiple apps for same provider (without client_id filter)
        app1 = SocialApp.objects.create(
            provider='github',
            name='GitHub App 1',
            client_id='github-1',
            secret='secret-1'
        )
        app1.sites.add(site)
        
        app2 = SocialApp.objects.create(
            provider='github',
            name='GitHub App 2',
            client_id='github-2',
            secret='secret-2'
        )
        app2.sites.add(site)
        
        result = adapter.get_app(request_obj, 'github')
        
        # Should return first match (app1)
        assert result == app1
    
    def test_get_app_filters_by_site(self, adapter, request_obj, site):
        """Test that get_app only returns apps for the request's site."""
        # Create another site
        other_site = Site.objects.create(domain='other.com', name='Other Site')
        
        # Create app for different site
        other_app = SocialApp.objects.create(
            provider='google',
            name='Google for Other Site',
            client_id='other-client',
            secret='other-secret'
        )
        other_app.sites.add(other_site)
        
        # Should raise DoesNotExist since app is not associated with request.site
        with pytest.raises(SocialApp.DoesNotExist):
            adapter.get_app(request_obj, 'google')
    
    def test_get_app_with_client_id_not_found(self, adapter, request_obj, site):
        """Test that get_app raises DoesNotExist when client_id doesn't match."""
        app = SocialApp.objects.create(
            provider='google',
            name='Google OAuth',
            client_id='correct-id',
            secret='secret'
        )
        app.sites.add(site)
        
        # Try to get with wrong client_id
        with pytest.raises(SocialApp.DoesNotExist):
            adapter.get_app(request_obj, 'google', client_id='wrong-id')
