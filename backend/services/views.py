from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Service
from .serializers import ServiceSerializer, ServiceRegistrationSerializer


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for service management.
    
    - List: Available to all authenticated users
    - Register: Open endpoint for services to register themselves
    - Update/Delete: Only system admins
    """
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    
    def get_permissions(self):
        """Allow service registration without authentication."""
        if self.action == 'register':
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def list(self, request):
        """List all active services."""
        services = self.get_queryset()
        serializer = self.get_serializer(services, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a service with AUTHinator.
        
        Services call this endpoint on startup to register themselves.
        Requires a valid service_key.
        """
        serializer = ServiceRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            service = serializer.save()
            response_serializer = ServiceSerializer(service)
            return Response(
                {
                    'detail': f'Service {service.name} registered successfully',
                    'service': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
