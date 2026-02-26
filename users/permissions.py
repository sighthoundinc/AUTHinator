"""
Custom permission classes for user management.
"""
from rest_framework import permissions


class IsSystemAdminOrCustomerAdmin(permissions.BasePermission):
    """
    Permission class that allows access to system admins and customer admins.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_system_admin() or request.user.is_customer_admin()
