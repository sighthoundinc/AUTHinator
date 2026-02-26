"""
Authentication views for Authinator.

Provides JWT-based authentication endpoints:
- login: Generate access and refresh tokens
- refresh: Refresh access token
- logout: Blacklist refresh token
- me: Get current user information
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate

from .serializers import LoginSerializer, UserSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for monitoring service availability.
    
    Returns:
        200 OK with service status
    """
    return Response({
        'status': 'healthy',
        'service': 'authinator',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login endpoint that generates JWT tokens.
    
    Request body:
        username: User's username
        password: User's password
    
    Returns:
        200: Success with access and refresh tokens
        400: Missing credentials
        401: Invalid credentials
        403: User not verified or inactive
    """
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    # Authenticate user
    user = authenticate(request, username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Check if user is verified
    if not user.is_verified:
        return Response(
            {'detail': 'User account is not verified. Please wait for admin approval.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if user is active
    if not user.is_active:
        return Response(
            {'detail': 'User account is inactive'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Generate tokens
    refresh = RefreshToken.for_user(user)
    
    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    Refresh access token using refresh token.
    
    Request body:
        refresh: Valid refresh token
    
    Returns:
        200: Success with new access token
        400: Missing refresh token or invalid token
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)
    except TokenError as e:
        return Response(
            {'detail': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def logout(request):
    """
    Logout by blacklisting the refresh token.
    
    Request body:
        refresh: Refresh token to blacklist
    
    Returns:
        200: Success
        400: Missing refresh token or invalid token
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'detail': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(
            {'detail': 'Successfully logged out'},
            status=status.HTTP_200_OK
        )
    except TokenError as e:
        return Response(
            {'detail': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """
    Get current authenticated user information.
    
    Returns:
        200: User information including customer details
        401: Not authenticated
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)
