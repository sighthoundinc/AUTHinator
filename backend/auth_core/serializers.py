"""
Serializers for authentication and user management.
"""
from rest_framework import serializers
from users.models import User, Customer


class CustomerSerializer(serializers.ModelSerializer):
    """Serializer for Customer model."""
    
    class Meta:
        model = Customer
        fields = ['id', 'name', 'contact_email', 'is_active']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model.
    Includes nested customer information.
    """
    customer = CustomerSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'customer', 'role', 'is_verified', 'is_active'
        ]
        read_only_fields = ['id', 'is_verified']


class LoginSerializer(serializers.Serializer):
    """Serializer for login requests."""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    customer_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'customer_id', 'role'
        ]
        extra_kwargs = {
            'email': {'validators': []},  # Disable default validators, we'll add custom validation
        }
    
    def validate_username(self, value):
        """Validate username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        """Validate email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, attrs):
        """Validate password match and customer existence."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        
        # Validate customer exists
        customer_id = attrs.get('customer_id')
        try:
            customer = Customer.objects.get(id=customer_id)
            if not customer.is_active:
                raise serializers.ValidationError({"customer_id": "Customer is not active."})
            attrs['customer'] = customer
        except Customer.DoesNotExist:
            raise serializers.ValidationError({"customer_id": "Invalid customer ID."})
        
        # Prevent users from registering as admin
        role = attrs.get('role', User.USER)
        if role == User.ADMIN:
            attrs['role'] = User.USER
        
        return attrs
    
    def create(self, validated_data):
        """Create new user with unverified status."""
        validated_data.pop('password_confirm')
        customer = validated_data.pop('customer')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            customer=customer,
            password=password,
            is_verified=False,
            is_active=True,  # Active but not verified
            **validated_data
        )
        return user


class UserApprovalSerializer(serializers.Serializer):
    """Serializer for user approval."""
    pass  # No fields needed for approval


class UserRejectionSerializer(serializers.Serializer):
    """Serializer for user rejection."""
    reason = serializers.CharField(required=True, max_length=500)
