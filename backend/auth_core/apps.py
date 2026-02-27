from django.apps import AppConfig


class AuthCoreConfig(AppConfig):
    name = 'auth_core'
    
    def ready(self):
        # Import signals to register them
        import auth_core.signals
