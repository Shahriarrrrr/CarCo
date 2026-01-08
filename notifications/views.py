from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from notifications.models import Notification, NotificationPreference
from notifications.serializers import NotificationSerializer, NotificationPreferenceSerializer


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for notifications."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user notifications.
    
    Features:
    - List user notifications
    - Mark notifications as read
    - Mark all notifications as read
    - Filter by type
    """
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get notifications for current user."""
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read."""
        notification = self.get_object()
        
        # Check permission
        if notification.user != request.user:
            return Response(
                {'error': 'You can only mark your own notifications as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.mark_as_read()
        return Response(
            {'message': 'Notification marked as read'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read."""
        notifications = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        count = notifications.update(is_read=True)
        
        return Response(
            {'message': f'{count} notifications marked as read'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications."""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response(
            {'unread_count': count},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get notifications by type."""
        notification_type = request.query_params.get('type')
        
        if not notification_type:
            return Response(
                {'error': 'type parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = Notification.objects.filter(
            user=request.user,
            notification_type=notification_type
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications."""
        queryset = Notification.objects.filter(
            user=request.user,
            is_read=False
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class NotificationPreferenceViewSet(viewsets.ViewSet):
    """
    ViewSet for notification preferences.
    
    Features:
    - Get notification preferences
    - Update notification preferences
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get notification preferences for current user."""
        try:
            preferences = request.user.notification_preferences
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            preferences = NotificationPreference.objects.create(user=request.user)
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)
    
    def update(self, request, pk=None):
        """Update notification preferences."""
        try:
            preferences = request.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=request.user)
        
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {'message': 'Preferences updated', 'preferences': serializer.data},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's notification preferences."""
        try:
            preferences = request.user.notification_preferences
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)
        except NotificationPreference.DoesNotExist:
            # Create default preferences
            preferences = NotificationPreference.objects.create(user=request.user)
            serializer = NotificationPreferenceSerializer(preferences)
            return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update notification preferences."""
        try:
            preferences = request.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=request.user)
        
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {'message': 'Preferences updated', 'preferences': serializer.data},
            status=status.HTTP_200_OK
        )
