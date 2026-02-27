"""
Django admin configuration for User and Customer models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Customer, User


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """
    Admin interface for Customer model.
    """
    list_display = ('name', 'contact_email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'contact_email')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'contact_email', 'contact_phone', 'billing_address')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for custom User model.
    Extends Django's UserAdmin to include custom fields.
    """
    list_display = ('username', 'email', 'customer', 'role', 'is_verified', 'is_active')
    list_filter = ('role', 'is_verified', 'is_active', 'customer')
    search_fields = ('username', 'email', 'customer__name')
    ordering = ('customer', 'username')
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Customer & Role', {
            'fields': ('customer', 'role')
        }),
        ('Verification', {
            'fields': ('is_verified', 'verified_at', 'verified_by', 'rejection_reason')
        }),
    )
    
    readonly_fields = ['verified_at']
