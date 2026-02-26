from django.db import models
from django.utils import timezone


class Service(models.Model):
    """
    Registered service in the authentication ecosystem.
    Services can register themselves to appear in the Authinator service directory.
    """
    name = models.CharField(max_length=100, unique=True, help_text="Display name of the service")
    description = models.TextField(help_text="Description shown to users")
    base_url = models.URLField(help_text="Base URL for API calls")
    api_prefix = models.CharField(max_length=50, help_text="API prefix (e.g., /api/fulfil)")
    ui_url = models.URLField(help_text="Frontend URL for user access")
    icon = models.CharField(max_length=10, default="🔷", help_text="Emoji icon for display")
    service_key = models.CharField(max_length=255, help_text="Secret key for service registration")
    is_active = models.BooleanField(default=True, help_text="Whether service is active and visible")
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_registered_at = models.DateTimeField(null=True, blank=True, help_text="Last time service registered")
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def mark_registered(self):
        """Mark that the service has registered/re-registered."""
        self.last_registered_at = timezone.now()
        self.save(update_fields=['last_registered_at'])
