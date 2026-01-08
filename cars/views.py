from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from cars.models import Car, CarImage, CarSpecification
from cars.serializers import (
    CarListSerializer, CarDetailSerializer, CarCreateUpdateSerializer,
    CarImageSerializer, CarSearchSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for car listings."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners to edit their cars."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller == request.user


class CarViewSet(viewsets.ModelViewSet):
    """
    ViewSet for car listings.
    
    Features:
    - List all active cars
    - Create new car listings (authenticated sellers)
    - Search and filter cars
    - View car details
    - Update/delete own listings
    - Upload car images
    - Mark cars as sold
    """
    
    queryset = Car.objects.filter(status='active')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['make', 'model', 'title', 'description', 'city']
    ordering_fields = ['price', 'created_at', 'year', 'mileage']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return CarDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CarCreateUpdateSerializer
        elif self.action == 'search':
            return CarSearchSerializer
        return CarListSerializer
    
    def get_queryset(self):
        """Filter queryset based on user and status."""
        queryset = Car.objects.all()
        
        # Non-staff users only see active cars or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(status='active') | Q(seller=self.request.user)
            )
        
        return queryset.select_related('seller').prefetch_related('images')
    
    def create(self, request, *args, **kwargs):
        """Create a new car listing."""
        if not request.user.is_seller:
            return Response(
                {'error': 'Only sellers can create car listings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            CarDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )
    
    def perform_create(self, serializer):
        """Save car with seller from request user."""
        serializer.save(seller=self.request.user)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced search for cars with filters.
        
        Query parameters:
        - make: Car make
        - model: Car model
        - year_from: Minimum year
        - year_to: Maximum year
        - price_from: Minimum price
        - price_to: Maximum price
        - condition: Car condition
        - fuel_type: Fuel type
        - transmission: Transmission type
        - city: City
        - mileage_max: Maximum mileage
        - search: General search term
        """
        serializer = self.get_serializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        filters_data = serializer.validated_data
        
        # Apply filters
        if 'make' in filters_data:
            queryset = queryset.filter(make__icontains=filters_data['make'])
        
        if 'model' in filters_data:
            queryset = queryset.filter(model__icontains=filters_data['model'])
        
        if 'year_from' in filters_data:
            queryset = queryset.filter(year__gte=filters_data['year_from'])
        
        if 'year_to' in filters_data:
            queryset = queryset.filter(year__lte=filters_data['year_to'])
        
        if 'price_from' in filters_data:
            queryset = queryset.filter(price__gte=filters_data['price_from'])
        
        if 'price_to' in filters_data:
            queryset = queryset.filter(price__lte=filters_data['price_to'])
        
        if 'condition' in filters_data:
            queryset = queryset.filter(condition=filters_data['condition'])
        
        if 'fuel_type' in filters_data:
            queryset = queryset.filter(fuel_type=filters_data['fuel_type'])
        
        if 'transmission' in filters_data:
            queryset = queryset.filter(transmission=filters_data['transmission'])
        
        if 'city' in filters_data:
            queryset = queryset.filter(city__icontains=filters_data['city'])
        
        if 'mileage_max' in filters_data:
            queryset = queryset.filter(mileage__lte=filters_data['mileage_max'])
        
        if 'search' in filters_data:
            search_term = filters_data['search']
            queryset = queryset.filter(
                Q(make__icontains=search_term) |
                Q(model__icontains=search_term) |
                Q(title__icontains=search_term) |
                Q(description__icontains=search_term)
            )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CarListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CarListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_images(self, request, pk=None):
        """Upload images for a car."""
        car = self.get_object()
        
        # Check permission
        if car.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only upload images for your own cars'},
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
            car_image = CarImage.objects.create(car=car, image=image)
            created_images.append(CarImageSerializer(car_image).data)
        
        return Response(
            {'images': created_images},
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def mark_as_sold(self, request, pk=None):
        """Mark a car as sold."""
        car = self.get_object()
        
        # Check permission
        if car.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only mark your own cars as sold'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        car.mark_as_sold()
        return Response(
            {'message': 'Car marked as sold', 'car': CarDetailSerializer(car).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get current user's car listings."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = Car.objects.filter(seller=request.user).select_related('seller').prefetch_related('images')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = CarListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CarListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def seller_cars(self, request):
        """Get cars from a specific seller."""
        seller_id = request.query_params.get('seller_id')
        if not seller_id:
            return Response(
                {'error': 'seller_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Car.objects.filter(
            seller_id=seller_id,
            status='active'
        ).select_related('seller').prefetch_related('images')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CarListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CarListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def set_primary_image(self, request, pk=None):
        """Set primary image for a car."""
        car = self.get_object()
        
        # Check permission
        if car.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only modify your own car images'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        image_id = request.data.get('image_id')
        if not image_id:
            return Response(
                {'error': 'image_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = CarImage.objects.get(id=image_id, car=car)
            image.is_primary = True
            image.save()
            return Response(
                {'message': 'Primary image set', 'image': CarImageSerializer(image).data},
                status=status.HTTP_200_OK
            )
        except CarImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
