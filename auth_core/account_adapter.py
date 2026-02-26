"""
Custom account adapter for Authinator.
Handles automatic signup for SSO users.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter to handle auto-signup.
    """
    
    def is_open_for_signup(self, request):
        """
        Allow signups via SSO.
        """
        return True


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to auto-complete signup.
    """
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Allow automatic signup for all SSO providers.
        Return True to skip the signup form.
        """
        return True
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user from social account data.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Ensure email is set
        if not user.email and data.get('email'):
            user.email = data['email']
        
        # Mark as verified since they logged in via trusted provider
        user.is_verified = True
        
        return user
