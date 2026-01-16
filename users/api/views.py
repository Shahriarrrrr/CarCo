from users.models import CustomUser
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db import models
from users.api.serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
    ChangePasswordSerializer,
    UserListSerializer
)


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner
        return obj == request.user


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management including registration, login, and profile management.
    """
    queryset = CustomUser.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'register']:
            return UserRegistrationSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        elif self.action == 'retrieve' or self.action == 'list':
            if self.action == 'retrieve':
                return UserProfileSerializer
            return UserListSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        return UserProfileSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'register', 'login']:
            permission_classes = [AllowAny]
        elif self.action in ['update', 'partial_update', 'change_password', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter queryset based on user permissions and query parameters."""
        queryset = CustomUser.objects.all()
        
        # Base filtering for non-staff users
        if not self.request.user.is_staff:
            # Regular users can only see verified sellers and themselves
            queryset = queryset.filter(
                models.Q(verification_status='verified') | models.Q(id=self.request.user.id)
            )
        
        # Filter by verification status (available to all users)
        verification_status = self.request.query_params.get('verification_status')
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        # Filter by user type
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # Filter by seller status
        is_seller = self.request.query_params.get('is_seller')
        if is_seller is not None:
            queryset = queryset.filter(is_seller=is_seller.lower() in ['true', '1'])
        
        # Filter by email verification
        email_verified = self.request.query_params.get('email_verified')
        if email_verified is not None:
            queryset = queryset.filter(email_verified=email_verified.lower() in ['true', '1'])
        
        # Filter by phone verification
        phone_verified = self.request.query_params.get('phone_verified')
        if phone_verified is not None:
            queryset = queryset.filter(phone_verified=phone_verified.lower() in ['true', '1'])
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Create a new user account."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User created successfully',
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """
        Register a new user.
        
        Expected fields:
        - email: User email
        - password: User password
        - password2: Password confirmation
        - first_name: User first name
        - last_name: User last name
        - phone_number: Optional phone number
        - user_type: 'individual' or 'company'
        - company_name: Required if user_type is 'company'
        - company_registration_number: Required if user_type is 'company'
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """
        Login user and return JWT tokens.
        
        Expected fields:
        - email: User email
        - password: User password
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            
            user = authenticate(request, username=email, password=password)
            if user is not None:
                user.update_last_login()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'user': UserProfileSerializer(user).data,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Invalid email or password'
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """
        Change user password.
        
        Expected fields:
        - old_password: Current password
        - new_password: New password
        - new_password2: New password confirmation
        """
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def enable_seller(self, request):
        """Enable seller mode for the user."""
        user = request.user
        if user.verification_status != 'verified':
            return Response({
                'error': 'Account must be verified before enabling seller mode'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.is_seller = True
        user.save()
        return Response({
            'message': 'Seller mode enabled',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def disable_seller(self, request):
        """Disable seller mode for the user."""
        user = request.user
        user.is_seller = False
        user.save()
        return Response({
            'message': 'Seller mode disabled',
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def sellers(self, request):
        """List all verified sellers."""
        sellers = CustomUser.objects.filter(
            is_seller=True,
            verification_status='verified',
            is_active=True
        )
        serializer = UserListSerializer(sellers, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """Get user profile by ID."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update user profile."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user is updating their own profile
        if instance != request.user and not request.user.is_staff:
            return Response({
                'error': 'You can only update your own profile'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return Response(UserProfileSerializer(instance).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, *args, **kwargs):
        """Delete user account (soft delete by deactivating)."""
        instance = self.get_object()
        
        # Check if user is deleting their own account
        if instance != request.user and not request.user.is_staff:
            return Response({
                'error': 'You can only delete your own account'
            }, status=status.HTTP_403_FORBIDDEN)
        
        instance.is_active = False
        instance.save()
        return Response({
            'message': 'Account deactivated successfully'
        }, status=status.HTTP_204_NO_CONTENT)


# Import models for queryset filtering
from django.db import models