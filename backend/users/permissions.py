"""
Custom permission classes for user management.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class that allows access only to admin users.
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated and has admin role."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.is_admin()


# Legacy alias
IsSystemAdminOrCustomerAdmin = IsAdmin
