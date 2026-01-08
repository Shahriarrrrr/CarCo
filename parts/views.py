from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from parts.models import CarPart, PartImage, PartCategory, PartCompatibility, CompanyStore
from parts.serializers import (
    PartListSerializer, PartDetailSerializer, PartCreateUpdateSerializer,
    PartImageSerializer, PartCategorySerializer, PartCompatibilitySerializer,
    CompanyStoreSerializer, PartSearchSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for part listings."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners to edit their parts."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller == request.user


class CarPartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for car parts listings.
    
    Features:
    - List all active parts
    - Create new part listings (authenticated sellers)
    - Search and filter parts
    - View part details
    - Update/delete own listings
    - Upload part images
    - Track compatibility
    """
    
    queryset = CarPart.objects.filter(status='active')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'brand', 'description', 'part_number']
    ordering_fields = ['price', 'created_at', 'rating', 'quantity_in_stock']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return PartDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PartCreateUpdateSerializer
        elif self.action == 'search':
            return PartSearchSerializer
        return PartListSerializer
    
    def get_queryset(self):
        """Filter queryset based on user and status."""
        queryset = CarPart.objects.all()
        
        # Non-staff users only see active parts or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='active') | Q(seller=self.request.user)
            )
        
        return queryset.select_related('seller', 'category').prefetch_related('images', 'compatibilities')
    
    def create(self, request, *args, **kwargs):
        """Create a new part listing."""
        if not request.user.is_seller:
            return Response(
                {'error': 'Only sellers can create part listings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            PartDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )
    
    def perform_create(self, serializer):
        """Save part with seller from request user."""
        serializer.save(seller=self.request.user)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for parts with filters.
        
        Query parameters:
        - name: Part name
        - category: Category UUID
        - brand: Brand name
        - condition: Part condition
        - price_from: Minimum price
        - price_to: Maximum price
        - in_stock_only: Only in-stock items
        - search: General search term
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        filters_data = serializer.validated_data
        
        # Apply filters
        if 'name' in filters_data:
            queryset = queryset.filter(name__icontains=filters_data['name'])
        
        if 'category' in filters_data:
            queryset = queryset.filter(category_id=filters_data['category'])
        
        if 'brand' in filters_data:
            queryset = queryset.filter(brand__icontains=filters_data['brand'])
        
        if 'condition' in filters_data:
            queryset = queryset.filter(condition=filters_data['condition'])
        
        if 'price_from' in filters_data:
            queryset = queryset.filter(price__gte=filters_data['price_from'])
        
        if 'price_to' in filters_data:
            queryset = queryset.filter(price__lte=filters_data['price_to'])
        
        if filters_data.get('in_stock_only'):
            queryset = queryset.filter(quantity_in_stock__gt=0, status='active')
        
        if 'search' in filters_data:
            search_term = filters_data['search']
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(brand__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(part_number__icontains=search_term)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PartListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PartListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Upload images for a part."""
        part = self.get_object()
        
        # Check permission
        if part.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only upload images for your own parts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_images = []
        for image in images:
            part_image = PartImage.objects.create(part=part, image=image)
            created_images.append(PartImageSerializer(part_image).data)
        
        return Response(
            {'images': created_images},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def compatible_cars(self, request, pk=None):
        """Get compatible cars for a part."""
        part = self.get_object()
        compatibilities = part.compatibilities.all()
        serializer = PartCompatibilitySerializer(compatibilities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_compatibility(self, request, pk=None):
        """Add car compatibility for a part."""
        part = self.get_object()
        
        # Check permission
        if part.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only modify your own parts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = PartCompatibilitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        compatibility = PartCompatibility.objects.create(part=part, **serializer.validated_data)
        return Response(
            PartCompatibilitySerializer(compatibility).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get current user's part listings."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = CarPart.objects.filter(seller=request.user).select_related('seller', 'category').prefetch_related('images')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = PartListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PartListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get parts by category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = CarPart.objects.filter(
            category_id=category_id,
            status='active'
        ).select_related('seller', 'category').prefetch_related('images')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PartListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = PartListSerializer(queryset, many=True)
        return Response(serializer.data)


class PartCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for part categories."""
    
    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class CompanyStoreViewSet(viewsets.ModelViewSet):
    """ViewSet for company stores."""
    
    queryset = CompanyStore.objects.filter(is_active=True)
    serializer_class = CompanyStoreSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['store_name', 'store_description']
    ordering_fields = ['store_rating', 'created_at']
    ordering = ['-store_rating']
    
    def create(self, request, *args, **kwargs):
        """Create a company store."""
        if request.user.user_type != 'company':
            return Response(
                {'error': 'Only company accounts can create stores'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if hasattr(request.user, 'store_profile'):
            return Response(
                {'error': 'You already have a store'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(company=request.user)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def my_store(self, request):
        """Get current user's store."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            store = request.user.store_profile
            serializer = self.get_serializer(store)
            return Response(serializer.data)
        except CompanyStore.DoesNotExist:
            return Response(
                {'error': 'Store not found'},
                status=status.HTTP_404_NOT_FOUND
            )
