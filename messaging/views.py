from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils import timezone
from messaging.models import (
    Conversation, Message, MessageAttachment, ConversationParticipant,
    TypingIndicator, BlockedUser
)
from messaging.serializers import (
    ConversationListSerializer, ConversationDetailSerializer,
    ConversationCreateSerializer, MessageSerializer, MessageCreateSerializer,
    MessageAttachmentSerializer, ConversationParticipantSerializer,
    TypingIndicatorSerializer, BlockedUserSerializer
)


class MessagePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations.
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = MessagePagination
    
    def get_queryset(self):
        """Get conversations for the current user."""
        user = self.request.user
        return Conversation.objects.filter(
            participants=user,
            is_active=True
        ).distinct().order_by('-last_message_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        elif self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationListSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if direct message conversation already exists
        participant_ids = serializer.validated_data.get('participant_ids', [])
        if len(participant_ids) == 1:
            # Direct message - check if conversation exists
            existing = Conversation.objects.filter(
                conversation_type='direct',
                participants=request.user
            ).filter(participants__id__in=participant_ids).distinct()
            
            if existing.exists():
                return Response(
                    ConversationListSerializer(existing.first(), context={'request': request}).data,
                    status=status.HTTP_200_OK
                )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get messages in a conversation."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = conversation.messages.all()
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = MessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark all messages in conversation as read."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Mark all messages as read
        for message in conversation.messages.all():
            message.mark_as_read(request.user)
        
        # Update participant data
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=request.user
        )
        last_message = conversation.messages.last()
        if last_message:
            participant.mark_as_read(last_message)
        
        return Response({'status': 'All messages marked as read'})
    
    @action(detail=True, methods=['post'])
    def add_participant(self, request, pk=None):
        """Add a participant to the conversation."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            conversation.add_participant(user)
            return Response({'status': 'Participant added'})
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the conversation."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        try:
            user = CustomUser.objects.get(id=user_id)
            conversation.remove_participant(user)
            return Response({'status': 'Participant removed'})
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a conversation."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=request.user
        )
        participant.is_archived = True
        participant.save()
        
        return Response({'status': 'Conversation archived'})
    
    @action(detail=True, methods=['post'])
    def mute(self, request, pk=None):
        """Mute a conversation."""
        conversation = self.get_object()
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        participant = ConversationParticipant.objects.get(
            conversation=conversation,
            user=request.user
        )
        participant.is_muted = True
        participant.save()
        
        return Response({'status': 'Conversation muted'})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing messages.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer
    pagination_class = MessagePagination
    
    def get_queryset(self):
        """Get messages for conversations the user is part of."""
        user = self.request.user
        return Message.objects.filter(
            conversation__participants=user
        ).distinct().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MessageCreateSerializer
        return MessageSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new message."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = serializer.validated_data['conversation']
        
        # Check if user is participant
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {'detail': 'You are not a participant in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user is blocked
        if BlockedUser.objects.filter(
            blocker__in=conversation.participants.all(),
            blocked_user=request.user
        ).exists():
            return Response(
                {'detail': 'You are blocked from sending messages in this conversation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        self.perform_create(serializer)
        
        # Update conversation last message time
        conversation.update_last_message()
        conversation.message_count += 1
        conversation.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a message as read."""
        message = self.get_object()
        message.mark_as_read(request.user)
        return Response({'status': 'Message marked as read'})
    
    @action(detail=True, methods=['put'])
    def edit(self, request, pk=None):
        """Edit a message."""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'detail': 'You can only edit your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.content = request.data.get('content', message.content)
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save()
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=True, methods=['delete'])
    def delete_message(self, request, pk=None):
        """Delete a message."""
        message = self.get_object()
        
        # Check if user is the sender
        if message.sender != request.user:
            return Response(
                {'detail': 'You can only delete your own messages.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.delete()
        return Response({'status': 'Message deleted'}, status=status.HTTP_204_NO_CONTENT)


class BlockedUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing blocked users.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BlockedUserSerializer
    
    def get_queryset(self):
        """Get blocked users for the current user."""
        return BlockedUser.objects.filter(blocker=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Block a user."""
        blocked_user_id = request.data.get('blocked_user')
        reason = request.data.get('reason', '')
        
        try:
            blocked_user = CustomUser.objects.get(id=blocked_user_id)
            
            # Check if already blocked
            if BlockedUser.objects.filter(
                blocker=request.user,
                blocked_user=blocked_user
            ).exists():
                return Response(
                    {'detail': 'User is already blocked.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            blocked = BlockedUser.objects.create(
                blocker=request.user,
                blocked_user=blocked_user,
                reason=reason
            )
            
            serializer = self.get_serializer(blocked)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except CustomUser.DoesNotExist:
            return Response(
                {'detail': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a user."""
        blocked = self.get_object()
        blocked.delete()
        return Response({'status': 'User unblocked'})


from users.models import CustomUser
