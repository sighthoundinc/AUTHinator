"""
Management command to configure SSO providers from environment variables.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Configure SSO providers from environment variables'

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        
        # Configure Site domain from DEPLOY_DOMAIN (for OAuth callback URLs)
        deploy_domain = getattr(settings, 'DEPLOY_DOMAIN', '')
        if deploy_domain:
            site.domain = deploy_domain
            site.name = deploy_domain
        else:
            # Use unified gateway for local dev
            site.domain = 'localhost:8080'
            site.name = 'Inator Platform (dev)'
        site.save()
        self.stdout.write(
            self.style.SUCCESS(f'Site domain set to: {site.domain}')
        )
        
        # Configure Google
        if settings.SSO_PROVIDER_CREDENTIALS['google']['enabled']:
            google_app, created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': settings.SSO_PROVIDER_CREDENTIALS['google']['client_id'],
                    'secret': settings.SSO_PROVIDER_CREDENTIALS['google']['secret'],
                }
            )
            google_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'{"Created" if created else "Updated"} Google SSO app')
            )
        else:
            self.stdout.write(self.style.WARNING('Google SSO not configured (no credentials)'))
        
        # Configure Microsoft
        if settings.SSO_PROVIDER_CREDENTIALS['microsoft']['enabled']:
            microsoft_app, created = SocialApp.objects.update_or_create(
                provider='microsoft',
                defaults={
                    'name': 'Microsoft',
                    'client_id': settings.SSO_PROVIDER_CREDENTIALS['microsoft']['client_id'],
                    'secret': settings.SSO_PROVIDER_CREDENTIALS['microsoft']['secret'],
                }
            )
            microsoft_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'{"Created" if created else "Updated"} Microsoft SSO app')
            )
        else:
            self.stdout.write(self.style.WARNING('Microsoft SSO not configured (no credentials)'))
        
        # Configure Auth0
        if settings.SSO_PROVIDER_CREDENTIALS['auth0']['enabled']:
            auth0_app, created = SocialApp.objects.update_or_create(
                provider='auth0',
                defaults={
                    'name': 'Auth0',
                    'client_id': settings.SSO_PROVIDER_CREDENTIALS['auth0']['client_id'],
                    'secret': settings.SSO_PROVIDER_CREDENTIALS['auth0']['secret'],
                    'key': settings.SSO_PROVIDER_CREDENTIALS['auth0']['domain'],
                }
            )
            auth0_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'{"Created" if created else "Updated"} Auth0 SSO app')
            )
        else:
            self.stdout.write(self.style.WARNING('Auth0 SSO not configured (no credentials)'))
        
        # Configure Okta
        if settings.SSO_PROVIDER_CREDENTIALS['okta']['enabled']:
            okta_app, created = SocialApp.objects.update_or_create(
                provider='okta',
                defaults={
                    'name': 'Okta',
                    'client_id': settings.SSO_PROVIDER_CREDENTIALS['okta']['client_id'],
                    'secret': settings.SSO_PROVIDER_CREDENTIALS['okta']['secret'],
                }
            )
            okta_app.sites.add(site)
            self.stdout.write(
                self.style.SUCCESS(f'{"Created" if created else "Updated"} Okta SSO app')
            )
        else:
            self.stdout.write(self.style.WARNING('Okta SSO not configured (no credentials)'))
        
        self.stdout.write(self.style.SUCCESS('\nSSO setup complete!'))
