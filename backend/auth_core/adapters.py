"""
Custom adapters for allauth to handle SSO properly.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.socialaccount.models import SocialApp


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom adapter to handle SSO provider configuration.
    Overrides get_app to prevent MultipleObjectsReturned errors.
    """
    
    def get_app(self, request, provider, client_id=None):
        """
        Override to get apps safely, returning first match to avoid MultipleObjectsReturned.
        """
        # Directly query for apps instead of calling super() which raises exception
        apps = SocialApp.objects.filter(
            provider=provider,
            sites__id=request.site.id
        )
        if client_id:
            apps = apps.filter(client_id=client_id)
        
        # Return first match or raise DoesNotExist
        app = apps.first()
        if not app:
            raise SocialApp.DoesNotExist(
                f"SocialApp matching query for provider {provider} does not exist."
            )
        return app
