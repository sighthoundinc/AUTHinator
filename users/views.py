"""
Views for user management and approval workflow.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import User
from auth_core.serializers import (
    RegistrationSerializer, 
    UserSerializer,
    UserApprovalSerializer,
    UserRejectionSerializer
)
from users.permissions import IsSystemAdminOrCustomerAdmin


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Public endpoint for user registration.
    Creates unverified user and sends notification to admins.
    """
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send notification email to system admins
        self._notify_admins_new_registration(user)
        
        # Return user data
        response_serializer = UserSerializer(user)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def _notify_admins_new_registration(self, user):
        """Send email notification to system admins about new registration."""
        admin_emails = User.objects.filter(
            role=User.SYSTEM_ADMIN,
            is_active=True
        ).values_list('email', flat=True)
        
        if admin_emails:
            send_mail(
                subject=f'New User Registration - {user.username}',
                message=f'A new user has registered and is awaiting approval:\n\n'
                        f'Username: {user.username}\n'
                        f'Email: {user.email}\n'
                        f'Name: {user.first_name} {user.last_name}\n'
                        f'Customer: {user.customer.name}\n\n'
                        f'Please review and approve or reject this registration.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=list(admin_emails),
                fail_silently=True,
            )


class PendingUsersView(generics.ListAPIView):
    """
    GET /api/users/pending/
    List all users awaiting approval.
    Only accessible to system admins and customer admins.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSystemAdminOrCustomerAdmin]
    pagination_class = None  # Disable pagination for this endpoint
    
    def get_queryset(self):
        """Return pending users based on user role."""
        user = self.request.user
        
        if user.is_system_admin():
            # System admins see all pending users
            return User.objects.filter(is_verified=False).select_related('customer')
        elif user.is_customer_admin():
            # Customer admins only see their customer's pending users
            return User.objects.filter(
                is_verified=False,
                customer=user.customer
            ).select_related('customer')
        
        return User.objects.none()


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSystemAdminOrCustomerAdmin])
def approve_user(request, pk):
    """
    POST /api/users/{id}/approve/
    Approve a pending user.
    Only accessible to system admins and customer admins.
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions
    if not request.user.is_system_admin():
        # Customer admins can only approve users from their own customer
        if not request.user.is_customer_admin() or user.customer != request.user.customer:
            return Response(
                {'detail': 'You do not have permission to approve this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Check if already verified
    if user.is_verified:
        return Response(
            {'detail': 'User is already verified.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Approve user
    user.is_verified = True
    user.verified_at = timezone.now()
    user.verified_by = request.user
    user.rejection_reason = None  # Clear any previous rejection
    user.save()
    
    # Send approval email
    send_mail(
        subject='Your Account Has Been Approved',
        message=f'Hello {user.first_name},\n\n'
                f'Your account has been approved! You can now log in to the system.\n\n'
                f'Username: {user.username}\n\n'
                f'Thank you!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSystemAdminOrCustomerAdmin])
def reject_user(request, pk):
    """
    POST /api/users/{id}/reject/
    Reject a pending user with a reason.
    Only accessible to system admins and customer admins.
    """
    try:
        user = User.objects.get(pk=pk)
    except User.DoesNotExist:
        return Response(
            {'detail': 'User not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check permissions
    if not request.user.is_system_admin():
        # Customer admins can only reject users from their own customer
        if not request.user.is_customer_admin() or user.customer != request.user.customer:
            return Response(
                {'detail': 'You do not have permission to reject this user.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
    # Validate request data
    serializer = UserRejectionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Reject user
    user.rejection_reason = serializer.validated_data['reason']
    user.is_verified = False  # Ensure still not verified
    user.save()
    
    # Send rejection email
    send_mail(
        subject='Your Account Registration - Rejected',
        message=f'Hello {user.first_name},\n\n'
                f'Unfortunately, your account registration has been rejected.\n\n'
                f'Reason: {user.rejection_reason}\n\n'
                f'If you have any questions, please contact your administrator.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=True,
    )
    
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)
