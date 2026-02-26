"""
URL configuration for AUTHinator.

Routes:
    /admin/ - Django admin interface
    /api/auth/ - Authentication endpoints
    /api/users/ - User management endpoints
    /api/services/ - Service registry endpoints
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from auth_core.views import health_check, login, refresh_token, logout, me
from auth_core.sso_views import sso_providers
from auth_core.sso_callback import SSOCallbackView
from users.views import RegisterView, PendingUsersView, approve_user, reject_user
from services.views import ServiceViewSet

# Router for service registry
router = DefaultRouter()
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('admin/', admin.site.urls),
    # Authentication endpoints
    path('api/auth/health/', health_check, name='health-check'),
    path('api/auth/login/', login, name='login'),
    path('api/auth/refresh/', refresh_token, name='refresh'),
    path('api/auth/logout/', logout, name='logout'),
    path('api/auth/me/', me, name='me'),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/sso-providers/', sso_providers, name='sso-providers'),
    # User management endpoints
    path('api/users/pending/', PendingUsersView.as_view(), name='pending-users'),
    path('api/users/<int:pk>/approve/', approve_user, name='approve-user'),
    path('api/users/<int:pk>/reject/', reject_user, name='reject-user'),
    # Service registry
    path('api/', include(router.urls)),
    # SSO callback after successful login
    path('accounts/profile/', SSOCallbackView.as_view(), name='sso-callback'),
    # Allauth URLs for SSO
    path('accounts/', include('allauth.urls')),
]
