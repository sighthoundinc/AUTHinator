from rest_framework import serializers
from .models import Service


class ServiceSerializer(serializers.ModelSerializer):
    """Serializer for Service model - used for listing services."""
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'description', 'ui_url', 'icon', 'is_active', 'last_registered_at']
        read_only_fields = ['id', 'last_registered_at']


class ServiceRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for service registration - includes service_key validation."""
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'base_url', 'api_prefix', 'ui_url', 'icon', 'service_key']
        extra_kwargs = {
            'service_key': {'write_only': True}
        }
    
    def validate_service_key(self, value):
        """Validate service key matches the configured key."""
        from django.conf import settings
        if value != settings.SERVICE_REGISTRATION_KEY:
            raise serializers.ValidationError("Invalid service registration key")
        return value
    
    def create(self, validated_data):
        """Create or update service on registration."""
        name = validated_data['name']
        
        # Update if service already exists, otherwise create
        service, created = Service.objects.update_or_create(
            name=name,
            defaults=validated_data
        )
        
        service.mark_registered()
        return service
