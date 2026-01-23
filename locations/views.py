from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import PermissionDenied
from django.db.models import Q
from .models import ShopLocation
from .serializers import (
    ShopLocationSerializer,
    ShopLocationCreateSerializer,
    ShopLocationPublicSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for listings."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ShopLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shop locations.
    
    Features:
    - Sellers can create location requests
    - Admin can approve/reject locations via admin panel
    - Public can view approved locations for the map
    - Sellers can view and manage their own locations
    
    Endpoints:
    - GET /api/shop-locations/ - List locations (filtered by user permissions)
    - POST /api/shop-locations/ - Create location request (sellers only)
    - GET /api/shop-locations/{id}/ - Get location detail
    - PUT/PATCH /api/shop-locations/{id}/ - Update location (owner or admin)
    - DELETE /api/shop-locations/{id}/ - Delete location (owner or admin)
    - GET /api/shop-locations/public_map/ - Get all approved locations for map
    - GET /api/shop-locations/my_locations/ - Get current user's locations
    - GET /api/shop-locations/pending_approvals/ - Admin: Get pending locations
    - POST /api/shop-locations/{id}/approve/ - Admin: Approve location
    - POST /api/shop-locations/{id}/reject/ - Admin: Reject location
    """
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'city', 'description']
    ordering_fields = ['created_at', 'name', 'city', 'approval_status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        queryset = ShopLocation.objects.select_related('seller', 'store', 'approved_by')
        
        # Public/unauthenticated users only see approved and active locations
        if not self.request.user.is_authenticated:
            return queryset.filter(approval_status='approved', is_active=True)
        
        # Admin sees all locations
        if self.request.user.is_staff:
            # Optional filter by approval status for admin
            status_filter = self.request.query_params.get('approval_status')
            if status_filter:
                queryset = queryset.filter(approval_status=status_filter)
            return queryset
        
        # Sellers see their own locations + approved locations from others
        if self.request.user.is_seller:
            return queryset.filter(
                Q(seller=self.request.user) | 
                Q(approval_status='approved', is_active=True)
            )
        
        # Regular authenticated users see only approved locations
        return queryset.filter(approval_status='approved', is_active=True)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ShopLocationCreateSerializer
        elif self.action in ['list', 'retrieve'] and not self.request.user.is_authenticated:
            return ShopLocationPublicSerializer
        elif self.action == 'public_map':
            return ShopLocationPublicSerializer
        return ShopLocationSerializer
    
    def perform_create(self, serializer):
        """Create location with current user as seller."""
        if not self.request.user.is_seller:
            raise PermissionDenied('Only sellers can create shop locations')
        
        # Save with pending approval status
        serializer.save(
            seller=self.request.user,
            approval_status='pending'
        )
    
    def update(self, request, *args, **kwargs):
        """Update location (only by owner or admin)."""
        location = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or location.seller == request.user):
            return Response(
                {'error': 'You do not have permission to update this location'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If seller is updating, reset approval status to pending
        if location.seller == request.user and not request.user.is_staff:
            location.approval_status = 'pending'
            location.approved_at = None
            location.approved_by = None
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """Delete location (only by owner or admin)."""
        location = self.get_object()
        
        # Check permissions
        if not (request.user.is_staff or location.seller == request.user):
            return Response(
                {'error': 'You do not have permission to delete this location'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def approve(self, request, pk=None):
        """
        Approve a shop location (admin only).
        
        Admin can also approve locations directly from the admin panel,
        but this endpoint is provided for API-based approval.
        """
        location = self.get_object()
        
        if location.approval_status == 'approved':
            return Response(
                {'error': 'Location is already approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        location.approve(request.user)
        
        return Response(
            {
                'message': 'Location approved successfully',
                'location': ShopLocationSerializer(location, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def reject(self, request, pk=None):
        """
        Reject a shop location (admin only).
        
        Admin can also reject locations directly from the admin panel,
        but this endpoint is provided for API-based rejection.
        """
        location = self.get_object()
        reason = request.data.get('reason', '')
        
        if location.approval_status == 'rejected':
            return Response(
                {'error': 'Location is already rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        location.reject(request.user, reason)
        
        return Response(
            {
                'message': 'Location rejected',
                'reason': reason,
                'location': ShopLocationSerializer(location, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def my_locations(self, request):
        """Get current user's shop locations (all statuses)."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = ShopLocation.objects.filter(
            seller=request.user
        ).select_related('store', 'approved_by').order_by('-created_at')
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ShopLocationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ShopLocationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public_map(self, request):
        """
        Get all approved locations for public map display.
        
        This endpoint is used by the frontend map to display all approved locations.
        No authentication required - public endpoint.
        
        Optional query parameters:
        - type: Filter by location_type (shop, service, warehouse)
        - city: Filter by city (case-insensitive contains)
        """
        queryset = ShopLocation.objects.filter(
            approval_status='approved',
            is_active=True
        ).select_related('seller', 'store')
        
        # Optional filters
        location_type = request.query_params.get('type')
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        serializer = ShopLocationPublicSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def pending_approvals(self, request):
        """
        Get locations pending approval (admin only).
        
        This endpoint can be used by admin interfaces to show pending approval queue.
        However, the main approval workflow should be through Django admin panel.
        """
        queryset = ShopLocation.objects.filter(
            approval_status='pending'
        ).select_related('seller', 'store').order_by('created_at')
        
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ShopLocationSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ShopLocationSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get location statistics (admin or seller for own stats)."""
        if request.user.is_staff:
            # Admin sees all stats
            total = ShopLocation.objects.count()
            approved = ShopLocation.objects.filter(approval_status='approved').count()
            pending = ShopLocation.objects.filter(approval_status='pending').count()
            rejected = ShopLocation.objects.filter(approval_status='rejected').count()
            active = ShopLocation.objects.filter(is_active=True, approval_status='approved').count()
        elif request.user.is_seller:
            # Sellers see their own stats
            total = ShopLocation.objects.filter(seller=request.user).count()
            approved = ShopLocation.objects.filter(seller=request.user, approval_status='approved').count()
            pending = ShopLocation.objects.filter(seller=request.user, approval_status='pending').count()
            rejected = ShopLocation.objects.filter(seller=request.user, approval_status='rejected').count()
            active = ShopLocation.objects.filter(seller=request.user, is_active=True, approval_status='approved').count()
        else:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'total': total,
            'approved': approved,
            'pending': pending,
            'rejected': rejected,
            'active': active
        })
