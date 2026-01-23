from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from forum.models import (
    ForumCategory, ForumThread, ForumResponse, ExpertVerification, ResponseVote
)
from forum.serializers import (
    ForumCategorySerializer, ForumThreadListSerializer, ForumThreadDetailSerializer,
    ForumThreadCreateUpdateSerializer, ForumResponseSerializer, ForumResponseCreateSerializer,
    ExpertVerificationSerializer, ExpertVerificationRequestSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for forum."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners to edit their content."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class ForumCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for forum categories."""
    
    queryset = ForumCategory.objects.filter(is_active=True)
    serializer_class = ForumCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class ForumThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for forum threads.
    
    Features:
    - Create discussion threads
    - Search and filter threads
    - View thread details with responses
    - Update/delete own threads
    - Mark threads as resolved
    - Pin/feature threads (staff only)
    """
    
    queryset = ForumThread.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'car_make', 'car_model']
    ordering_fields = ['created_at', 'responses_count', 'views_count']
    ordering = ['-is_pinned', '-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return ForumThreadDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ForumThreadCreateUpdateSerializer
        return ForumThreadListSerializer
    
    def get_queryset(self):
        """Filter queryset based on status."""
        return self.queryset.select_related('author', 'category').prefetch_related('responses')
    
    def create(self, request, *args, **kwargs):
        """Create a new forum thread."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(
            ForumThreadDetailSerializer(serializer.instance).data,
            status=status.HTTP_201_CREATED
        )
    
    def perform_create(self, serializer):
        """Save thread with author from request user."""
        serializer.save(author=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Retrieve thread and increment view count."""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        """Mark thread as resolved."""
        thread = self.get_object()
        
        # Check permission
        if thread.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only thread author or staff can mark as resolved'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        thread.mark_as_resolved()
        return Response(
            {'message': 'Thread marked as resolved', 'thread': ForumThreadDetailSerializer(thread).data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_response(self, request, pk=None):
        """Add a response to a thread."""
        thread = self.get_object()
        
        serializer = ForumResponseCreateSerializer(
            data=request.data,
            context={'request': request, 'thread': thread}
        )
        serializer.is_valid(raise_exception=True)
        response = serializer.save()  # Signal will update thread.responses_count automatically
        
        return Response(
            ForumResponseSerializer(response).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_threads(self, request):
        """Get current user's threads."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = ForumThread.objects.filter(author=request.user).select_related('author', 'category')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ForumThreadListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ForumThreadListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get threads by category."""
        category_id = request.query_params.get('category_id')
        if not category_id:
            return Response(
                {'error': 'category_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = ForumThread.objects.filter(category_id=category_id).select_related('author', 'category')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = ForumThreadListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ForumThreadListSerializer(queryset, many=True)
        return Response(serializer.data)


class ForumResponseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for forum responses.
    
    Features:
    - Create responses to threads
    - Vote on response helpfulness
    - Update/delete own responses
    - Mark expert responses
    """
    
    queryset = ForumResponse.objects.filter(is_approved=True)
    serializer_class = ForumResponseSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'helpful_count']
    ordering = ['-is_expert_response', '-helpful_count', 'created_at']
    
    def get_queryset(self):
        """Filter queryset based on user."""
        queryset = ForumResponse.objects.all()
        
        # Non-staff users only see approved responses or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_approved=True) | Q(author=self.request.user)
            )
        
        # Filter by thread if provided
        thread_id = self.request.query_params.get('thread')
        if thread_id:
            queryset = queryset.filter(thread_id=thread_id)
        
        return queryset.select_related('author', 'thread').prefetch_related('votes')
    
    @action(detail=True, methods=['post'])
    def vote(self, request, pk=None):
        """Vote on response helpfulness."""
        response = self.get_object()
        vote_type = request.data.get('vote_type')
        
        if vote_type not in ['helpful', 'unhelpful']:
            return Response(
                {'error': 'vote_type must be "helpful" or "unhelpful"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create vote
        vote, created = ResponseVote.objects.get_or_create(
            response=response,
            user=request.user,
            defaults={'vote_type': vote_type}
        )
        
        # If vote exists and is different, update it
        if not created and vote.vote_type != vote_type:
            vote.vote_type = vote_type
            vote.save()  # Signal will update counts automatically
        
        # Refresh response to get updated counts from signal
        response.refresh_from_db()
        
        return Response(
            {
                'message': 'Vote recorded' if created else 'Vote updated',
                'response': ForumResponseSerializer(response, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['delete'])
    def remove_vote(self, request, pk=None):
        """Remove vote from response."""
        response = self.get_object()
        
        try:
            vote = ResponseVote.objects.get(response=response, user=request.user)
            vote.delete()  # Signal will update counts automatically
            
            # Refresh response to get updated counts
            response.refresh_from_db()
            
            return Response(
                {
                    'message': 'Vote removed',
                    'response': ForumResponseSerializer(response, context={'request': request}).data
                },
                status=status.HTTP_200_OK
            )
        except ResponseVote.DoesNotExist:
            return Response(
                {'error': 'Vote not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def my_responses(self, request):
        """Get current user's responses."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        queryset = ForumResponse.objects.filter(author=request.user).select_related('author', 'thread')
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ExpertVerificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for expert verification.
    
    Features:
    - Request expert verification
    - View verified experts
    - Manage expert profile
    """
    
    queryset = ExpertVerification.objects.filter(status='approved')
    serializer_class = ExpertVerificationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'expertise_areas']
    ordering_fields = ['verified_at', 'helpful_responses']
    ordering = ['-verified_at']
    
    def create(self, request, *args, **kwargs):
        """Request expert verification."""
        if hasattr(request.user, 'expert_verification'):
            return Response(
                {'error': 'You already have an expert verification request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ExpertVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        expert = ExpertVerification.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        return Response(
            ExpertVerificationSerializer(expert).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def my_verification(self, request):
        """Get current user's expert verification status."""
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            expert = request.user.expert_verification
            serializer = ExpertVerificationSerializer(expert)
            return Response(serializer.data)
        except ExpertVerification.DoesNotExist:
            return Response(
                {'error': 'No expert verification found'},
                status=status.HTTP_404_NOT_FOUND
            )
