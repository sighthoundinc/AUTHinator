"""
Signal handlers for SSO authentication.
"""
from allauth.socialaccount.signals import pre_social_login
from django.dispatch import receiver
from users.models import Customer


@receiver(pre_social_login)
def handle_social_login(sender, request, sociallogin, **kwargs):
    """
    Handle social login by auto-creating user if needed.
    """
    # If user is already connected, nothing to do
    if sociallogin.is_existing:
        return
    
    # Check if user with this email already exists
    email = sociallogin.account.extra_data.get('email')
    if not email:
        # Try to get email from other fields
        email = (sociallogin.account.extra_data.get('mail') or 
                sociallogin.account.extra_data.get('userPrincipalName'))
    
    if email:
        # Check if user exists with this email
        from users.models import User
        try:
            user = User.objects.get(email=email)
            # Connect the social account to existing user
            sociallogin.connect(request, user)
        except User.DoesNotExist:
            # User will be created by allauth
            pass
