"""
Tests for User and Customer models.

Following Deft TDD: Tests written BEFORE implementation runs.
Target: ≥85% coverage
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone
from users.models import Customer, User


@pytest.mark.django_db
class TestCustomerModel:
    """Test suite for Customer model."""
    
    def test_create_customer_success(self):
        """Test creating a customer with valid data."""
        customer = Customer.objects.create(
            name="Acme Corp",
            contact_email="contact@acme.com",
            contact_phone="555-0100",
            billing_address="123 Main St"
        )
        assert customer.id is not None
        assert customer.name == "Acme Corp"
        assert customer.contact_email == "contact@acme.com"
        assert customer.is_active is True
        assert customer.created_at is not None
        assert customer.updated_at is not None
    
    def test_customer_str_representation(self):
        """Test __str__ method returns customer name."""
        customer = Customer.objects.create(
            name="Test Company",
            contact_email="test@test.com"
        )
        assert str(customer) == "Test Company"
    
    def test_customer_name_uniqueness(self):
        """Test that customer names must be unique."""
        Customer.objects.create(
            name="Unique Corp",
            contact_email="unique@test.com"
        )
        with pytest.raises(IntegrityError):
            Customer.objects.create(
                name="Unique Corp",
                contact_email="another@test.com"
            )
    
    def test_customer_optional_fields(self):
        """Test creating customer with minimal required fields."""
        customer = Customer.objects.create(
            name="Minimal Corp",
            contact_email="minimal@test.com"
        )
        assert customer.contact_phone == ""
        assert customer.billing_address == ""
    
    def test_customer_is_active_default(self):
        """Test that is_active defaults to True."""
        customer = Customer.objects.create(
            name="Active Corp",
            contact_email="active@test.com"
        )
        assert customer.is_active is True
    
    def test_customer_ordering(self):
        """Test customers are ordered by name."""
        Customer.objects.create(name="Zebra Corp", contact_email="z@test.com")
        Customer.objects.create(name="Alpha Corp", contact_email="a@test.com")
        Customer.objects.create(name="Beta Corp", contact_email="b@test.com")
        
        customers = list(Customer.objects.all())
        assert customers[0].name == "Alpha Corp"
        assert customers[1].name == "Beta Corp"
        assert customers[2].name == "Zebra Corp"


@pytest.mark.django_db
class TestUserModel:
    """Test suite for User model."""
    
    @pytest.fixture
    def customer(self):
        """Create a test customer."""
        return Customer.objects.create(
            name="Test Customer",
            contact_email="customer@test.com"
        )
    
    def test_create_user_with_customer(self, customer):
        """Test creating a user associated with a customer."""
        user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        assert user.id is not None
        assert user.username == "testuser"
        assert user.customer == customer
        assert user.role == User.CUSTOMER_USER
        assert user.is_verified is False
    
    def test_create_system_admin(self):
        """Test creating a system admin without customer."""
        admin = User.objects.create_user(
            username="admin",
            email="admin@test.com",
            password="adminpass123",
            role=User.SYSTEM_ADMIN
        )
        assert admin.customer is None
        assert admin.role == User.SYSTEM_ADMIN
    
    def test_user_str_with_customer(self, customer):
        """Test __str__ includes customer name."""
        user = User.objects.create_user(
            username="john",
            customer=customer
        )
        assert str(user) == "john (Test Customer)"
    
    def test_user_str_without_customer(self):
        """Test __str__ without customer."""
        user = User.objects.create_user(
            username="admin",
            role=User.SYSTEM_ADMIN
        )
        assert str(user) == "admin"
    
    def test_user_role_choices(self):
        """Test all role choices are valid."""
        assert User.SYSTEM_ADMIN == 'SYSTEM_ADMIN'
        assert User.CUSTOMER_ADMIN == 'CUSTOMER_ADMIN'
        assert User.CUSTOMER_USER == 'CUSTOMER_USER'
        assert User.CUSTOMER_READONLY == 'CUSTOMER_READONLY'
        
        # Verify choices tuple
        role_values = [choice[0] for choice in User.ROLE_CHOICES]
        assert User.SYSTEM_ADMIN in role_values
        assert User.CUSTOMER_ADMIN in role_values
        assert User.CUSTOMER_USER in role_values
        assert User.CUSTOMER_READONLY in role_values
    
    def test_user_default_role(self, customer):
        """Test default role is CUSTOMER_USER."""
        user = User.objects.create_user(
            username="newuser",
            customer=customer
        )
        assert user.role == User.CUSTOMER_USER
    
    def test_is_system_admin_method(self):
        """Test is_system_admin() method."""
        admin = User.objects.create_user(
            username="admin",
            role=User.SYSTEM_ADMIN
        )
        user = User.objects.create_user(
            username="user",
            role=User.CUSTOMER_USER
        )
        assert admin.is_system_admin() is True
        assert user.is_system_admin() is False
    
    def test_is_customer_admin_method(self, customer):
        """Test is_customer_admin() method."""
        admin = User.objects.create_user(
            username="custadmin",
            customer=customer,
            role=User.CUSTOMER_ADMIN
        )
        user = User.objects.create_user(
            username="user",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        assert admin.is_customer_admin() is True
        assert user.is_customer_admin() is False
    
    def test_can_manage_users_method(self, customer):
        """Test can_manage_users() for different roles."""
        system_admin = User.objects.create_user(
            username="sysadmin",
            role=User.SYSTEM_ADMIN
        )
        customer_admin = User.objects.create_user(
            username="custadmin",
            customer=customer,
            role=User.CUSTOMER_ADMIN
        )
        regular_user = User.objects.create_user(
            username="user",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        readonly_user = User.objects.create_user(
            username="readonly",
            customer=customer,
            role=User.CUSTOMER_READONLY
        )
        
        assert system_admin.can_manage_users() is True
        assert customer_admin.can_manage_users() is True
        assert regular_user.can_manage_users() is False
        assert readonly_user.can_manage_users() is False
    
    def test_can_edit_data_method(self, customer):
        """Test can_edit_data() method."""
        system_admin = User.objects.create_user(
            username="sysadmin",
            role=User.SYSTEM_ADMIN
        )
        regular_user = User.objects.create_user(
            username="user",
            customer=customer,
            role=User.CUSTOMER_USER
        )
        readonly_user = User.objects.create_user(
            username="readonly",
            customer=customer,
            role=User.CUSTOMER_READONLY
        )
        
        assert system_admin.can_edit_data() is True
        assert regular_user.can_edit_data() is True
        assert readonly_user.can_edit_data() is False
    
    def test_user_verification_workflow(self, customer):
        """Test user verification fields."""
        user = User.objects.create_user(
            username="pending",
            customer=customer
        )
        admin = User.objects.create_user(
            username="admin",
            role=User.SYSTEM_ADMIN
        )
        
        # Initially unverified
        assert user.is_verified is False
        assert user.verified_at is None
        assert user.verified_by is None
        
        # Verify user
        user.is_verified = True
        user.verified_at = timezone.now()
        user.verified_by = admin
        user.save()
        
        assert user.is_verified is True
        assert user.verified_at is not None
        assert user.verified_by == admin
    
    def test_user_rejection_reason(self, customer):
        """Test rejection reason field."""
        user = User.objects.create_user(
            username="rejected",
            customer=customer
        )
        user.rejection_reason = "Invalid documentation"
        user.save()
        
        assert user.rejection_reason == "Invalid documentation"
    
    def test_customer_deletion_cascades_to_users(self, customer):
        """Test that deleting a customer deletes associated users."""
        user1 = User.objects.create_user(
            username="user1",
            customer=customer
        )
        user2 = User.objects.create_user(
            username="user2",
            customer=customer
        )
        
        user_ids = [user1.id, user2.id]
        customer.delete()
        
        # Users should be deleted
        assert User.objects.filter(id__in=user_ids).count() == 0
    
    def test_user_ordering(self, customer):
        """Test users are ordered by customer then username."""
        customer2 = Customer.objects.create(
            name="Another Customer",
            contact_email="another@test.com"
        )
        
        User.objects.create_user(username="zebra", customer=customer)
        User.objects.create_user(username="alpha", customer=customer)
        User.objects.create_user(username="beta", customer=customer2)
        
        users = list(User.objects.all())
        # Should be ordered by customer name, then username
        assert users[0].username == "beta"  # Another Customer
        assert users[1].username == "alpha"  # Test Customer
        assert users[2].username == "zebra"  # Test Customer


@pytest.mark.django_db
class TestUserModelEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_user_with_empty_customer_field(self):
        """Test user can exist without customer (system admin)."""
        user = User.objects.create_user(
            username="nocustomer",
            role=User.SYSTEM_ADMIN
        )
        assert user.customer is None
    
    def test_multiple_users_same_customer(self):
        """Test multiple users can belong to same customer."""
        customer = Customer.objects.create(
            name="Shared Customer",
            contact_email="shared@test.com"
        )
        user1 = User.objects.create_user(
            username="user1",
            customer=customer
        )
        user2 = User.objects.create_user(
            username="user2",
            customer=customer
        )
        
        assert customer.users.count() == 2
        assert user1.customer == user2.customer
    
    def test_customer_users_related_name(self):
        """Test accessing users through customer.users."""
        customer = Customer.objects.create(
            name="Related Test",
            contact_email="related@test.com"
        )
        User.objects.create_user(username="u1", customer=customer)
        User.objects.create_user(username="u2", customer=customer)
        User.objects.create_user(username="u3", customer=customer)
        
        users = customer.users.all()
        assert users.count() == 3
