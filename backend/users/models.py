"""
User and Customer models for AUTHinator.

Implements B2B multi-tenant model where:
- Customer = Company/organization
- User = Individual employee account within a company
- Multiple users can belong to one Customer
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import EmailValidator
from django.utils import timezone


class Customer(models.Model):
    """
    Customer represents a company or organization.
    Multiple users can belong to one customer.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Company or organization name"
    )
    contact_email = models.EmailField(
        validators=[EmailValidator()],
        help_text="Primary contact email for the customer"
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary contact phone number"
    )
    billing_address = models.TextField(
        blank=True,
        help_text="Billing address for the customer"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the customer account is active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return self.name


class CustomUserManager(UserManager):
    """Custom manager that auto-verifies superusers."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', 'ADMIN')
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('verified_at', timezone.now())
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    
    Adds:
    - Customer foreign key (many-to-one relationship)
    - Role field for RBAC
    - Verification status for admin approval workflow
    """
    
    objects = CustomUserManager()

    # Role choices
    ADMIN = 'ADMIN'
    USER = 'USER'
    
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (USER, 'User'),
    ]
    
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        help_text="Customer this user belongs to (null for system admins)"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=USER,
        help_text="User's role for access control"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Whether user has been approved by admin"
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When user was verified by admin"
    )
    verified_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_users',
        help_text="Admin who verified this user"
    )
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection if user was rejected"
    )
    totp_secret = models.CharField(
        max_length=32,
        blank=True,
        null=True,
        help_text="TOTP secret for two-factor authentication"
    )
    totp_enabled = models.BooleanField(
        default=False,
        help_text="Whether TOTP two-factor authentication is enabled"
    )
    webauthn_registration_challenge = models.TextField(
        blank=True,
        null=True,
        help_text="Temporary storage for WebAuthn registration challenge (base64)"
    )
    webauthn_registration_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Temporary storage for WebAuthn credential name during registration"
    )
    webauthn_auth_challenge = models.TextField(
        blank=True,
        null=True,
        help_text="Temporary storage for WebAuthn authentication challenge (base64)"
    )

    class Meta:
        ordering = ['customer', 'username']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        if self.customer:
            return f"{self.username} ({self.customer.name})"
        return self.username

    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.ADMIN

    # Legacy aliases for backward compatibility during migration
    def is_system_admin(self):
        return self.is_admin()

    def is_customer_admin(self):
        return self.is_admin()

    def can_manage_users(self):
        """Check if user can manage other users."""
        return self.is_admin()
