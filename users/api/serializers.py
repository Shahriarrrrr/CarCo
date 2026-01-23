from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from users.models import CustomUser


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email', 'password', 'password2', 'first_name', 'last_name',
            'phone_number', 'user_type', 'company_name', 'company_registration_number',
            'business_email', 'business_phone_number', 'e_tin', 'trade_license_number', 'nid_number'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, data):
        """Validate password match and company fields."""
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {'password': 'Password fields didn\'t match.'}
            )
        
        # Validate company fields if user_type is company
        if data.get('user_type') == 'company':
            if not data.get('company_name'):
                raise serializers.ValidationError(
                    {'company_name': 'Company name is required for company accounts.'}
                )
            if not data.get('company_registration_number'):
                raise serializers.ValidationError(
                    {'company_registration_number': 'Company registration number is required.'}
                )
        
        return data
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'}
    )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile display."""
    full_name = serializers.SerializerMethodField()
    seller_rating = serializers.DecimalField(max_digits=3, decimal_places=2, read_only=True)
    seller_reviews_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'profile_picture', 'bio',
            'street_address', 'city', 'state_province', 'postal_code', 'country',
            'user_type', 'company_name', 'company_website', 'business_email',
            'business_phone_number', 'e_tin', 'trade_license_number', 'nid_number',
            'email_verified', 'phone_verified', 'verification_status', 'verification_count',
            'is_seller', 'is_buyer', 'seller_rating', 'seller_reviews_count',
            'date_joined', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email', 'email_verified', 'phone_verified', 'verification_status',
            'seller_rating', 'seller_reviews_count', 'date_joined', 'updated_at'
        ]
    
    def get_full_name(self, obj):
        """Return user's full name."""
        return obj.get_full_name()


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'phone_number', 'date_of_birth',
            'profile_picture', 'bio', 'street_address', 'city',
            'state_province', 'postal_code', 'country', 'company_name',
            'company_registration_number', 'company_website', 'business_email',
            'business_phone_number', 'e_tin', 'trade_license_number', 'nid_number',
            'verification_count'
        ]
    
    def validate_phone_number(self, value):
        """Validate phone number format."""
        if value and len(value) < 9:
            raise serializers.ValidationError(
                'Phone number must be at least 9 digits.'
            )
        return value


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password."""
    old_password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, data):
        """Validate password change."""
        if data['new_password'] != data['new_password2']:
            raise serializers.ValidationError(
                {'new_password': 'Password fields didn\'t match.'}
            )
        return data
    
    def validate_old_password(self, value):
        """Validate old password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                'Old password is not correct.'
            )
        return value


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (limited info for privacy)."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = [
            'id', 'email', 'full_name', 'profile_picture', 'user_type',
            'company_name', 'is_seller', 'seller_rating', 'seller_reviews_count',
            'verification_status', 'date_joined'
        ]
        read_only_fields = fields
    
    def get_full_name(self, obj):
        """Return user's full name."""
        return obj.get_full_name()