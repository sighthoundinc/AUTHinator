"""
Tests for user registration and approval workflow.

Following Deft TDD: Tests written BEFORE implementation.
Target: ≥85% coverage

Tests for:
- POST /api/auth/register/ - User registration
- GET /api/users/pending/ - List pending approvals (admin)
- POST /api/users/{id}/approve/ - Approve user (admin)
- POST /api/users/{id}/reject/ - Reject user (admin)
"""
import pytest
from django.test import Client
from django.core import mail
from users.models import Customer, User


@pytest.mark.django_db
class TestRegistrationEndpoint:
    """Test suite for user registration."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    def test_register_new_user_success(self, customer):
        """Test successful user registration."""
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'New',
            'last_name': 'User',
            'customer_id': customer.id,
            'role': User.USER
        }, content_type='application/json')
        
        assert response.status_code == 201
        data = response.json()
        assert data['username'] == 'newuser'
        assert data['email'] == 'new@test.com'
        assert data['is_verified'] is False
        
        # Verify user was created in database
        user = User.objects.get(username='newuser')
        assert user.is_verified is False
        assert user.customer == customer
    
    def test_register_sends_email_to_admins(self, customer):
        """Test that registration sends notification email to admins."""
        # Create an admin user to receive the notification
        admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.ADMIN
        )
        admin.is_verified = True
        admin.save()
        
        client = Client()
        client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': customer.id
        }, content_type='application/json')
        
        # Check email was sent
        assert len(mail.outbox) == 1
        assert 'new user registration' in mail.outbox[0].subject.lower()
    
    def test_register_requires_password_confirmation(self, customer):
        """Test registration fails if passwords don't match."""
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'different',
            'customer_id': customer.id
        }, content_type='application/json')
        
        assert response.status_code == 400
        assert 'password' in response.json()
    
    def test_register_requires_unique_username(self, customer):
        """Test registration fails with duplicate username."""
        User.objects.create_user(
            username='existing',
            email='existing@test.com',
            customer=customer
        )
        
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'existing',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': customer.id
        }, content_type='application/json')
        
        assert response.status_code == 400
    
    def test_register_requires_unique_email(self, customer):
        """Test registration fails with duplicate email."""
        User.objects.create_user(
            username='existing',
            email='duplicate@test.com',
            customer=customer
        )
        
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'duplicate@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': customer.id
        }, content_type='application/json')
        
        assert response.status_code == 400
    
    def test_register_requires_valid_customer(self):
        """Test registration fails with invalid customer ID."""
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': 99999
        }, content_type='application/json')
        
        assert response.status_code == 400
    
    def test_register_defaults_to_customer_user_role(self, customer):
        """Test registration defaults to CUSTOMER_USER role."""
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': customer.id
        }, content_type='application/json')
        
        assert response.status_code == 201
        user = User.objects.get(username='newuser')
        assert user.role == User.USER
    
    def test_register_cannot_set_system_admin_role(self, customer):
        """Test users cannot register as system admin."""
        client = Client()
        response = client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'new@test.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'customer_id': customer.id,
            'role': User.ADMIN
        }, content_type='application/json')
        
        # Should either reject or default to CUSTOMER_USER
        if response.status_code == 201:
            user = User.objects.get(username='newuser')
            assert user.role != User.ADMIN


@pytest.mark.django_db
class TestPendingUsersEndpoint:
    """Test suite for listing pending user approvals."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def admin_user(self):
        """Create a system admin."""
        user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.ADMIN
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def admin_tokens(self, admin_user):
        """Get admin tokens."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        }, content_type='application/json')
        return response.json()
    
    def test_get_pending_users_as_admin(self, customer, admin_tokens):
        """Test admin can get list of pending users."""
        # Create pending users
        User.objects.create_user(username='pending1', customer=customer, is_verified=False)
        User.objects.create_user(username='pending2', customer=customer, is_verified=False)
        
        client = Client()
        response = client.get(
            '/api/users/pending/',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        assert all(not user['is_verified'] for user in data)
    
    def test_get_pending_users_requires_auth(self):
        """Test pending users endpoint requires authentication."""
        client = Client()
        response = client.get('/api/users/pending/')
        
        assert response.status_code == 401
    
    def test_get_pending_users_requires_admin(self, customer):
        """Test non-admin users cannot access pending users."""
        user = User.objects.create_user(
            username='regular',
            customer=customer,
            password='pass123',
            role=User.USER
        )
        user.is_verified = True
        user.save()
        
        # Login as regular user
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'regular',
            'password': 'pass123'
        }, content_type='application/json')
        tokens = response.json()
        
        # Try to access pending users
        response = client.get(
            '/api/users/pending/',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}'
        )
        
        assert response.status_code == 403


@pytest.mark.django_db
class TestApproveUserEndpoint:
    """Test suite for user approval."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def admin_user(self):
        """Create a system admin."""
        user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.ADMIN
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def admin_tokens(self, admin_user):
        """Get admin tokens."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        }, content_type='application/json')
        return response.json()
    
    @pytest.fixture
    def pending_user(self, customer):
        """Create a pending user."""
        return User.objects.create_user(
            username='pending',
            email='pending@test.com',
            password='pass123',
            customer=customer,
            is_verified=False
        )
    
    def test_approve_user_success(self, admin_user, admin_tokens, pending_user):
        """Test admin can approve a pending user."""
        client = Client()
        response = client.post(
            f'/api/users/{pending_user.id}/approve/',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        assert response.status_code == 200
        
        # Check user is now verified
        pending_user.refresh_from_db()
        assert pending_user.is_verified is True
        assert pending_user.verified_by == admin_user
        assert pending_user.verified_at is not None
    
    def test_approve_user_sends_email(self, admin_user, admin_tokens, pending_user):
        """Test approval sends email to user."""
        client = Client()
        client.post(
            f'/api/users/{pending_user.id}/approve/',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        # Check email was sent
        assert len(mail.outbox) == 1
        assert pending_user.email in mail.outbox[0].to
        assert 'approved' in mail.outbox[0].subject.lower()
    
    def test_approve_user_requires_admin(self, customer, pending_user):
        """Test non-admin cannot approve users."""
        regular_user = User.objects.create_user(
            username='regular',
            customer=customer,
            password='pass123',
            role=User.USER
        )
        regular_user.is_verified = True
        regular_user.save()
        
        # Login as regular user
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'regular',
            'password': 'pass123'
        }, content_type='application/json')
        tokens = response.json()
        
        # Try to approve user
        response = client.post(
            f'/api/users/{pending_user.id}/approve/',
            HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}'
        )
        
        assert response.status_code == 403


@pytest.mark.django_db
class TestRejectUserEndpoint:
    """Test suite for user rejection."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Corp",
            contact_email="test@test.com"
        )
    
    @pytest.fixture
    def admin_user(self):
        """Create a system admin."""
        user = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.ADMIN
        )
        user.is_verified = True
        user.save()
        return user
    
    @pytest.fixture
    def admin_tokens(self, admin_user):
        """Get admin tokens."""
        client = Client()
        response = client.post('/api/auth/login/', {
            'username': 'admin',
            'password': 'adminpass123'
        }, content_type='application/json')
        return response.json()
    
    @pytest.fixture
    def pending_user(self, customer):
        """Create a pending user."""
        return User.objects.create_user(
            username='pending',
            email='pending@test.com',
            password='pass123',
            customer=customer,
            is_verified=False
        )
    
    def test_reject_user_success(self, admin_tokens, pending_user):
        """Test admin can reject a pending user."""
        client = Client()
        response = client.post(
            f'/api/users/{pending_user.id}/reject/',
            {'reason': 'Invalid documentation'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        assert response.status_code == 200
        
        # Check rejection reason was saved
        pending_user.refresh_from_db()
        assert pending_user.rejection_reason == 'Invalid documentation'
        assert pending_user.is_verified is False
    
    def test_reject_user_requires_reason(self, admin_tokens, pending_user):
        """Test rejection requires a reason."""
        client = Client()
        response = client.post(
            f'/api/users/{pending_user.id}/reject/',
            {},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        assert response.status_code == 400
    
    def test_reject_user_sends_email(self, admin_tokens, pending_user):
        """Test rejection sends email to user."""
        client = Client()
        client.post(
            f'/api/users/{pending_user.id}/reject/',
            {'reason': 'Invalid documentation'},
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}'
        )
        
        # Check email was sent
        assert len(mail.outbox) == 1
        assert pending_user.email in mail.outbox[0].to
        assert 'rejected' in mail.outbox[0].subject.lower()
