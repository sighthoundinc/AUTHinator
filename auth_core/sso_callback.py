"""
SSO callback handling for Authinator.
After successful SSO login, create JWT token and redirect to frontend.
"""
from django.shortcuts import redirect
from django.views import View
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.socialaccount.models import SocialAccount
from users.models import User, Customer


class SSOCallbackView(View):
    """
    Handle SSO login callback.
    Creates or gets user, generates JWT tokens, and redirects to frontend with token.
    """
    
    def get(self, request):
        # User should be authenticated by allauth at this point
        if not request.user.is_authenticated:
            # If not authenticated, redirect to login
            return redirect('http://localhost:3000/login')
        
        user = request.user
        
        # Ensure user has a customer - create one if needed
        if not hasattr(user, 'customer') or user.customer is None:
            # Get user's email domain for customer name
            email_domain = user.email.split('@')[1] if user.email and '@' in user.email else 'Unknown'
            customer_name = email_domain.split('.')[0].title() if '.' in email_domain else email_domain.title()
            
            # Create a customer for this user
            customer = Customer.objects.create(name=f"{customer_name} Organization")
            user.customer = customer
            user.save()
        
        # Ensure user is verified and active
        if not user.is_verified:
            user.is_verified = True
            user.save()
        
        # Generate JWT tokens for the authenticated user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        # Get the 'next' parameter if it was passed through the login flow
        next_url = request.session.get('socialaccount_next_url', None)
        
        if next_url:
            # Redirect back to the service that initiated login
            return redirect(f'{next_url}?token={access_token}')
        else:
            # Redirect to Authinator frontend service directory
            return redirect(f'http://localhost:3000/?token={access_token}')
