from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from ratings.models import Review, Rating, ReviewHelpfulness
from ratings.serializers import ReviewSerializer, ReviewCreateSerializer, RatingSerializer
from users.models import CustomUser


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for reviews."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners to edit their reviews."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.reviewer == request.user


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for seller reviews.
    
    Features:
    - Create reviews for sellers
    - Vote on review helpfulness
    - Update/delete own reviews
    - Seller responses to reviews
    """
    
    queryset = Review.objects.filter(is_approved=True)
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating', 'helpful_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user."""
        queryset = Review.objects.all()
        
        # Non-staff users only see approved reviews or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_approved=True) | Q(reviewer=self.request.user)
            )
        
        return queryset.select_related('reviewer', 'seller')
    
    def create(self, request, *args, **kwargs):
        """Create a review for a seller."""
        seller_id = request.data.get('seller_id')
        
        if not seller_id:
            return Response(
                {'error': 'seller_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            seller = CustomUser.objects.get(id=seller_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Seller not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already reviewed
        if Review.objects.filter(reviewer=request.user, seller=seller).exists():
            return Response(
                {'error': 'You already reviewed this seller'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'seller': seller}
        )
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        
        # Update seller rating
        rating, _ = Rating.objects.get_or_create(seller=seller)
        rating.update_from_reviews()
        
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Update a review."""
        review = self.get_object()
        
        # Check permission
        if review.reviewer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'You can only update your own reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Update seller rating
        rating, _ = Rating.objects.get_or_create(seller=review.seller)
        rating.update_from_reviews()
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark review as helpful."""
        review = self.get_object()
        
        # Check if already voted
        vote, created = ReviewHelpfulness.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'vote_type': 'helpful'}
        )
        
        if created:
            review.helpful_count += 1
            review.save(update_fields=['helpful_count'])
            return Response(
                {'message': 'Review marked as helpful'},
                status=status.HTTP_201_CREATED
            )
        else:
            if vote.vote_type == 'unhelpful':
                review.unhelpful_count -= 1
                review.helpful_count += 1
                vote.vote_type = 'helpful'
                vote.save()
                review.save()
                return Response(
                    {'message': 'Vote updated'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Already marked as helpful'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def mark_unhelpful(self, request, pk=None):
        """Mark review as unhelpful."""
        review = self.get_object()
        
        # Check if already voted
        vote, created = ReviewHelpfulness.objects.get_or_create(
            review=review,
            user=request.user,
            defaults={'vote_type': 'unhelpful'}
        )
        
        if created:
            review.unhelpful_count += 1
            review.save(update_fields=['unhelpful_count'])
            return Response(
                {'message': 'Review marked as unhelpful'},
                status=status.HTTP_201_CREATED
            )
        else:
            if vote.vote_type == 'helpful':
                review.helpful_count -= 1
                review.unhelpful_count += 1
                vote.vote_type = 'unhelpful'
                vote.save()
                review.save()
                return Response(
                    {'message': 'Vote updated'},
                    status=status.HTTP_200_OK
                )
            return Response(
                {'message': 'Already marked as unhelpful'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=False, methods=['get'])
    def by_seller(self, request):
        """Get reviews for a specific seller."""
        seller_id = request.query_params.get('seller_id')
        
        if not seller_id:
            return Response(
                {'error': 'seller_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Review.objects.filter(
            seller_id=seller_id,
            is_approved=True
        ).select_related('reviewer', 'seller')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = Review.objects.filter(reviewer=request.user).select_related('reviewer', 'seller')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class SellerRatingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for seller ratings.
    
    Features:
    - View seller rating summary
    - View rating distribution
    - View aspect ratings
    """
    
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['average_rating', 'total_reviews']
    ordering = ['-average_rating']
    
    @action(detail=False, methods=['get'])
    def by_seller(self, request):
        """Get rating for a specific seller."""
        seller_id = request.query_params.get('seller_id')
        
        if not seller_id:
            return Response(
                {'error': 'seller_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rating = Rating.objects.get(seller_id=seller_id)
            serializer = self.get_serializer(rating)
            return Response(serializer.data)
        except Rating.DoesNotExist:
            return Response(
                {'error': 'Rating not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# Import Q for filtering
from django.db.models import Q
