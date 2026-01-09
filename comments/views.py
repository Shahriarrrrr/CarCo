from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment, CommentReply, CommentLike
from comments.serializers import (
    CommentSerializer, CommentReplySerializer, CommentCreateSerializer,
    CommentReplyCreateSerializer
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for comments."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Permission to only allow owners to edit their comments."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comments on cars and parts.
    
    Features:
    - Create comments on listings
    - Reply to comments
    - Like/unlike comments
    - Update/delete own comments
    """
    
    queryset = Comment.objects.filter(is_approved=True)
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user."""
        queryset = Comment.objects.all()
        
        # Non-staff users only see approved comments or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_approved=True) | Q(author=self.request.user)
            )
        
        return queryset.select_related('author').prefetch_related('replies')
    
    def create(self, request, *args, **kwargs):
        """Create a comment on a car or part."""
        content_type_str = request.data.get('content_type')
        object_id = request.data.get('object_id')
        
        if not content_type_str or not object_id:
            return Response(
                {'error': 'content_type and object_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate content type
        if content_type_str not in ['car', 'part']:
            return Response(
                {'error': 'content_type must be "car" or "part"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get content type
        if content_type_str == 'car':
            from cars.models import Car
            content_type = ContentType.objects.get_for_model(Car)
        else:
            from parts.models import CarPart
            content_type = ContentType.objects.get_for_model(CarPart)
        
        serializer = CommentCreateSerializer(
            data=request.data,
            context={
                'request': request,
                'content_type': content_type,
                'object_id': object_id
            }
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        
        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a comment."""
        comment = self.get_object()
        
        # Check if already liked
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            comment=comment,
            like_type='comment'
        )
        
        if created:
            comment.likes_count += 1
            comment.save(update_fields=['likes_count'])
            return Response(
                {'message': 'Comment liked'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already liked'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a comment."""
        comment = self.get_object()
        
        try:
            like = CommentLike.objects.get(
                user=request.user,
                comment=comment,
                like_type='comment'
            )
            like.delete()
            comment.likes_count -= 1
            comment.save(update_fields=['likes_count'])
            return Response(
                {'message': 'Comment unliked'},
                status=status.HTTP_200_OK
            )
        except CommentLike.DoesNotExist:
            return Response(
                {'error': 'Not liked'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Add a reply to a comment."""
        comment = self.get_object()
        
        serializer = CommentReplyCreateSerializer(
            data=request.data,
            context={'request': request, 'comment': comment}
        )
        serializer.is_valid(raise_exception=True)
        reply = serializer.save()
        
        # Update reply count
        comment.replies_count += 1
        comment.save(update_fields=['replies_count'])
        
        return Response(
            CommentReplySerializer(reply).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def by_object(self, request):
        """Get comments for a specific car or part."""
        content_type_str = request.query_params.get('content_type')
        object_id = request.query_params.get('object_id')
        
        if not content_type_str or not object_id:
            return Response(
                {'error': 'content_type and object_id parameters required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get content type
        if content_type_str == 'car':
            from cars.models import Car
            content_type = ContentType.objects.get_for_model(Car)
        elif content_type_str == 'part':
            from parts.models import CarPart
            content_type = ContentType.objects.get_for_model(CarPart)
        else:
            return Response(
                {'error': 'Invalid content_type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Comment.objects.filter(
            content_type=content_type,
            object_id=object_id,
            is_approved=True
        ).select_related('author').prefetch_related('replies')
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CommentReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for comment replies."""
    
    queryset = CommentReply.objects.filter(is_approved=True)
    serializer_class = CommentReplySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'likes_count']
    ordering = ['created_at']
    
    def get_queryset(self):
        """Filter queryset based on user."""
        queryset = CommentReply.objects.all()
        
        # Non-staff users only see approved replies or their own
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(is_approved=True) | Q(author=self.request.user)
            )
        
        return queryset.select_related('author', 'comment')
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like a reply."""
        reply = self.get_object()
        
        # Check if already liked
        like, created = CommentLike.objects.get_or_create(
            user=request.user,
            reply=reply,
            like_type='reply'
        )
        
        if created:
            reply.likes_count += 1
            reply.save(update_fields=['likes_count'])
            return Response(
                {'message': 'Reply liked'},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                {'message': 'Already liked'},
                status=status.HTTP_200_OK
            )
    
    @action(detail=True, methods=['post'])
    def unlike(self, request, pk=None):
        """Unlike a reply."""
        reply = self.get_object()
        
        try:
            like = CommentLike.objects.get(
                user=request.user,
                reply=reply,
                like_type='reply'
            )
            like.delete()
            reply.likes_count -= 1
            reply.save(update_fields=['likes_count'])
            return Response(
                {'message': 'Reply unliked'},
                status=status.HTTP_200_OK
            )
        except CommentLike.DoesNotExist:
            return Response(
                {'error': 'Not liked'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Import Q for filtering
from django.db.models import Q
