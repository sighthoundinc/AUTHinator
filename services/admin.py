from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'last_registered_at', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'last_registered_at']
    
    fieldsets = (
        ('Service Information', {
            'fields': ('name', 'description', 'icon', 'is_active')
        }),
        ('URLs', {
            'fields': ('base_url', 'api_prefix', 'ui_url')
        }),
        ('Security', {
            'fields': ('service_key',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_registered_at')
        }),
    )
