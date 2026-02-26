"""
SSO configuration views for AUTHinator frontend.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings


@api_view(['GET'])
@permission_classes([AllowAny])
def sso_providers(request):
    """
    Return list of enabled SSO providers based on database apps.
    Frontend uses this to display SSO login buttons.
    """
    from allauth.socialaccount.models import SocialApp
    
    providers = []
    
    # Get providers from database
    for app in SocialApp.objects.all():
        providers.append({
            'id': app.provider,
            'name': app.name,
            'login_url': f'/accounts/{app.provider}/login/',
        })
    
    return Response({'providers': providers})
