from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Avg
from parts.models import CarPart, PartImage, PartCategory, PartCompatibility, CompanyStore, PartReview, PartReviewHelpfulness
from parts.serializers import (
    PartListSerializer, PartDetailSerializer, PartCreateUpdateSerializer,
    PartImageSerializer, PartCategorySerializer, PartCompatibilitySerializer,
    CompanyStoreSerializer, PartSearchSerializer, PartReviewSerializer,
    PartReviewCreateSerializer, PartReviewHelpfulnessSerializer
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
            if self.request.user.is_authenticated:
                queryset = queryset.filter(
                    Q(status='active') | Q(seller=self.request.user)
                )
            else:
                queryset = queryset.filter(status='active')
        
        return queryset.select_related('seller', 'category').prefetch_related('images', 'compatibilities')
    
    def create(self, request, *args, **kwargs):
        """Create a new part listing with optional images."""
        if not request.user.is_seller:
            return Response(
                {'error': 'Only sellers can create part listings'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Handle images from FILES if present
        data = request.data.copy()
        images = request.FILES.getlist('images')
        if images:
            data['images'] = images
        
        serializer = self.get_serializer(data=data)
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


class PartReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for part reviews.
    
    Features:
    - Create reviews for parts
    - Vote on review helpfulness
    - Update/delete own reviews
    - Seller responses to reviews
    """
    
    queryset = PartReview.objects.filter(is_approved=True)
    serializer_class = PartReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    filterset_fields = ['is_verified_purchase', 'rating']
    
    def get_queryset(self):
        """Filter queryset based on user and query parameters."""
        queryset = PartReview.objects.all()
        
        # Non-staff users only see approved reviews or their own
        if not self.request.user.is_staff:
            if self.request.user.is_authenticated:
                queryset = queryset.filter(
                    Q(is_approved=True) | Q(reviewer=self.request.user)
                )
            else:
                queryset = queryset.filter(is_approved=True)
        
        # Filter by part
        part_id = self.request.query_params.get('part_id')
        if part_id:
            queryset = queryset.filter(part_id=part_id)
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified_purchase')
        if is_verified is not None:
            queryset = queryset.filter(is_verified_purchase=is_verified.lower() in ['true', '1'])
        
        # Filter by rating
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        
        # Filter by minimum rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)
        
        return queryset.select_related('reviewer', 'part')
    
    def create(self, request, *args, **kwargs):
        """Create a review for a part."""
        part_id = request.data.get('part_id')
        
        if not part_id:
            return Response(
                {'error': 'part_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            part = CarPart.objects.get(id=part_id)
        except CarPart.DoesNotExist:
            return Response(
                {'error': 'Part not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already reviewed
        if PartReview.objects.filter(reviewer=request.user, part=part).exists():
            return Response(
                {'error': 'You already reviewed this part'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PartReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'part': part}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Update part rating
        self._update_part_rating(part)
        
        return Response(
            PartReviewSerializer(review, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a review."""
        review = self.get_object()
        serializer = PartReviewCreateSerializer(
            review,
            data=request.data,
            partial=kwargs.get('partial', False),
            context={'request': request, 'part': review.part}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Update part rating
        self._update_part_rating(review.part)
        
        return Response(
            PartReviewSerializer(serializer.instance, context={'request': request}).data
        )
    
    def destroy(self, request, *args, **kwargs):
        """Delete a review."""
        review = self.get_object()
        part = review.part
        review.delete()
        
        # Update part rating
        self._update_part_rating(part)
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def vote_helpful(self, request, pk=None):
        """Mark review as helpful."""
        return self._handle_vote(request, pk, 'helpful')
    
    @action(detail=True, methods=['post'])
    def vote_unhelpful(self, request, pk=None):
        """Mark review as unhelpful."""
        return self._handle_vote(request, pk, 'unhelpful')
    
    @action(detail=True, methods=['delete'])
    def remove_vote(self, request, pk=None):
        """Remove vote from review."""
        review = self.get_object()
        
        vote = PartReviewHelpfulness.objects.filter(
            review=review,
            user=request.user
        ).first()
        
        if not vote:
            return Response(
                {'error': 'No vote found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update counts
        if vote.vote_type == 'helpful':
            review.helpful_count = max(0, review.helpful_count - 1)
        else:
            review.unhelpful_count = max(0, review.unhelpful_count - 1)
        review.save()
        
        vote.delete()
        
        return Response({'status': 'vote removed'})
    
    @action(detail=True, methods=['post'])
    def seller_respond(self, request, pk=None):
        """Seller responds to review."""
        review = self.get_object()
        
        if review.part.seller != request.user:
            return Response(
                {'error': 'Only the seller can respond to this review'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        response_text = request.data.get('response')
        if not response_text:
            return Response(
                {'error': 'Response text is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        review.seller_response = response_text
        review.seller_response_date = timezone.now()
        review.save()
        
        return Response(
            PartReviewSerializer(review, context={'request': request}).data
        )
    
    def _handle_vote(self, request, pk, vote_type):
        """Handle voting on a review."""
        review = self.get_object()
        
        # Check existing vote
        existing_vote = PartReviewHelpfulness.objects.filter(
            review=review,
            user=request.user
        ).first()
        
        if existing_vote:
            if existing_vote.vote_type == vote_type:
                return Response(
                    {'error': f'Already voted as {vote_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Change vote
            old_vote_type = existing_vote.vote_type
            existing_vote.vote_type = vote_type
            existing_vote.save()
            
            # Update counts
            if old_vote_type == 'helpful':
                review.helpful_count = max(0, review.helpful_count - 1)
                review.unhelpful_count += 1
            else:
                review.unhelpful_count = max(0, review.unhelpful_count - 1)
                review.helpful_count += 1
            review.save()
            
            return Response({'status': f'vote changed to {vote_type}'})
        
        # Create new vote
        PartReviewHelpfulness.objects.create(
            review=review,
            user=request.user,
            vote_type=vote_type
        )
        
        # Update count
        if vote_type == 'helpful':
            review.helpful_count += 1
        else:
            review.unhelpful_count += 1
        review.save()
        
        return Response({'status': f'voted as {vote_type}'})
    
    def _update_part_rating(self, part):
        """Update the part's average rating and review count."""
        reviews = PartReview.objects.filter(part=part, is_approved=True)
        
        part.reviews_count = reviews.count()
        
        if part.reviews_count > 0:
            avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
            part.rating = round(avg_rating, 2) if avg_rating else 0.0
        else:
            part.rating = 0.0
        
        part.save(update_fields=['rating', 'reviews_count'])
