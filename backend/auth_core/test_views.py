"""
Tests for auth_core views.

Following Deft TDD: Testing health check endpoint.
Target: ≥85% coverage
"""
import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
class TestHealthCheckView:
    """Test suite for health check endpoint."""
    
    def test_health_check_returns_200(self):
        """Test health check endpoint returns 200 OK."""
        client = Client()
        response = client.get('/api/auth/health/')
        assert response.status_code == 200
    
    def test_health_check_returns_correct_data(self):
        """Test health check returns expected JSON response."""
        client = Client()
        response = client.get('/api/auth/health/')
        data = response.json()
        
        assert data['status'] == 'healthy'
        assert data['service'] == 'AUTHinator'
        assert data['version'] == '1.0.0'
    
    def test_health_check_no_authentication_required(self):
        """Test health check can be accessed without authentication."""
        # Health check should work without any auth headers
        client = Client()
        response = client.get('/api/auth/health/')
        assert response.status_code == 200
