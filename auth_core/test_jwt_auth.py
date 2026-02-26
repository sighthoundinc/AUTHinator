"""
Tests for JWT authentication endpoints.

Following Deft TDD: Tests written BEFORE implementation.
Target: ≥85% coverage

Tests for:
- POST /api/auth/login/ - JWT token generation
- POST /api/auth/refresh/ - JWT token refresh
- POST /api/auth/logout/ - Token blacklisting
- GET /api/auth/me/ - Current user info
"""
import pytest
from django.test import Client
from django.urls import reverse
from users.models import Customer, User


@pytest.mark.django_db
class TestLoginEndpoint:
    """Test suite for login endpoint."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def verified_user(self, customer):
        """Create a verified user."""
        user = User.objects.create_user(
            username="testuser",
            email="user@test.com",
            password="testpass123",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def unverified_user(self, customer):
        """Create an unverified user."""
        return User.objects.create_user(
            username="unverified",
            email="unverified@test.com",
            password="testpass123",
            customer=customer,
            role=User.CUSTOMER_USER,
            is_verified=False
        )
    
    def test_login_with_valid_credentials(self, verified_user):
        """Test login with correct username and password returns tokens."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, content_type='application/json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        assert 'refresh' in data
        assert isinstance(data['access'], str)
        assert isinstance(data['refresh'], str)
    
    def test_login_with_invalid_password(self, verified_user):
        """Test login with wrong password fails."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, content_type='application/json')
        
        assert response.status_code == 401
    
    def test_login_with_nonexistent_user(self):
        """Test login with non-existent username fails."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'doesnotexist',
            'password': 'somepassword'
        }, content_type='application/json')
        
        assert response.status_code == 401
    
    def test_login_with_unverified_user(self, unverified_user):
        """Test unverified users cannot login."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'unverified',
            'password': 'testpass123'
        }, content_type='application/json')
        
        assert response.status_code == 403
        data = response.json()
        assert 'detail' in data
        assert 'not verified' in data['detail'].lower()
    
    def test_login_with_inactive_user(self, verified_user):
        """Test inactive users cannot login."""
        verified_user.is_active = False
        verified_user.save()
        
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, content_type='application/json')
        
        assert response.status_code in [401, 403]
    
    def test_login_requires_username(self, verified_user):
        """Test login fails without username."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'password': 'testpass123'
        }, content_type='application/json')
        
        assert response.status_code == 400
    
    def test_login_requires_password(self, verified_user):
        """Test login fails without password."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser'
        }, content_type='application/json')
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestRefreshEndpoint:
    """Test suite for token refresh endpoint."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def verified_user(self, customer):
        """Create a verified user."""
        user = User.objects.create_user(
            username="testuser",
            email="user@test.com",
            password="testpass123",
            customer=customer
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def tokens(self, verified_user):
        """Get valid tokens for a user."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, content_type='application/json')
        return response.json()
    
    def test_refresh_with_valid_token(self, tokens):
        """Test refreshing token with valid refresh token."""
        client = Client()
        response = client.post('/api/auth/refresh/', {
            'refresh': tokens['refresh']
        }, content_type='application/json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
        # New access token should be different from old one
        assert data['access'] != tokens['access']
    
    def test_refresh_with_invalid_token(self):
        """Test refresh fails with invalid token."""
        client = Client()
        response = client.post('/api/auth/refresh/', {
            'refresh': 'invalid.token.here'
        }, content_type='application/json')
        
        assert response.status_code in [401, 400]
    
    def test_refresh_requires_token(self):
        """Test refresh fails without token."""
        client = Client()
        response = client.post('/api/auth/refresh/', {}, content_type='application/json')
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Test suite for logout endpoint (token blacklisting)."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def verified_user(self, customer):
        """Create a verified user."""
        user = User.objects.create_user(
            username="testuser",
            email="user@test.com",
            password="testpass123",
            customer=customer
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def tokens(self, verified_user):
        """Get valid tokens for a user."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, content_type='application/json')
        return response.json()
    
    def test_logout_blacklists_token(self, tokens):
        """Test logout blacklists the refresh token."""
        client = Client()
        response = client.post('/api/auth/logout/', {
            'refresh': tokens['refresh']
        }, content_type='application/json')
        
        assert response.status_code == 200
        
        # Try to use the same refresh token again - should fail
        response = client.post('/api/auth/refresh/', {
            'refresh': tokens['refresh']
        }, content_type='application/json')
        
        assert response.status_code in [401, 400]
    
    def test_logout_requires_refresh_token(self):
        """Test logout fails without refresh token."""
        client = Client()
        response = client.post('/api/auth/logout/', {}, content_type='application/json')
        
        assert response.status_code == 400


@pytest.mark.django_db
class TestMeEndpoint:
    """Test suite for current user info endpoint."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def verified_user(self, customer):
        """Create a verified user."""
        user = User.objects.create_user(
            username="testuser",
            email="user@test.com",
            password="testpass123",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def tokens(self, verified_user):
        """Get valid tokens for a user."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, content_type='application/json')
        return response.json()
    
    def test_me_with_valid_token(self, verified_user, tokens):
        """Test /me endpoint returns current user info."""
        client = Client()
        response = client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == 'testuser'
        assert data['email'] == 'user@test.com'
        assert data['role'] == User.CUSTOMER_USER
        assert 'customer' in data
        assert data['customer']['name'] == 'Test Corp'
    
    def test_me_without_token_fails(self):
        """Test /me endpoint requires authentication."""
        client = Client()
        response = client.get('/api/auth/me/')
        
        assert response.status_code == 401
    
    def test_me_with_invalid_token_fails(self):
        """Test /me endpoint rejects invalid tokens."""
        client = Client()
        response = client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION='Bearer invalid.token.here'
        )
        
        assert response.status_code == 401


@pytest.mark.django_db
class TestJWTEdgeCases:
    """Test edge cases and security considerations."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def system_admin(self):
        """Create a system admin (no customer)."""
        user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.SYSTEM_ADMIN
        )
        user.is_verified = True
        user.save()
        return user
    
    def test_system_admin_login(self, system_admin):
        """Test system admin can login without customer."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        }, content_type='application/json')
        
        assert response.status_code == 200
        data = response.json()
        assert 'access' in data
    
    def test_system_admin_me_endpoint(self, system_admin):
        """Test /me endpoint works for system admin without customer."""
        client = Client()
        # Login
        response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        }, content_type='application/json')
        tokens = response.json()
        
        # Get user info
        response = client.get(
            '/api/auth/me/',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['username'] == 'admin'
        assert data['role'] == User.SYSTEM_ADMIN
        assert data['customer'] is None
