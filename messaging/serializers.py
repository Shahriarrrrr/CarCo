from rest_framework import serializers
from messaging.models import (
    Conversation, Message, MessageAttachment, ConversationParticipant,
    TypingIndicator, BlockedUser
)
from users.models import CustomUser


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for nested serialization."""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'profile_picture']
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for message attachments."""
    
    class Meta:
        model = MessageAttachment
        fields = [
            'id', 'file', 'file_name', 'file_size', 'attachment_type',
            'mime_type', 'width', 'height', 'duration', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for messages."""
    sender = UserBasicSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    read_count = serializers.SerializerMethodField()
    is_read_by_current_user = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = [
            'id', 'conversation', 'sender', 'message_type', 'content',
            'attachment', 'attachment_type', 'is_edited', 'edited_at',
            'attachments', 'read_count', 'is_read_by_current_user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sender', 'created_at', 'updated_at']
    
    def get_read_count(self, obj):
        return obj.get_read_count()
    
    def get_is_read_by_current_user(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.is_read_by_user(request.user)
        return False


class ConversationParticipantSerializer(serializers.ModelSerializer):
    """Serializer for conversation participants."""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = ConversationParticipant
        fields = [
            'id', 'user', 'is_muted', 'is_archived', 'is_blocked',
            'last_read_message', 'last_read_at', 'unread_count',
            'notifications_enabled', 'joined_at', 'left_at'
        ]
        read_only_fields = ['id', 'joined_at']


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for conversation list view."""
    participants = UserBasicSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'title', 'participants',
            'last_message', 'unread_count', 'other_participant',
            'is_active', 'last_message_at', 'message_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            participant = obj.participant_data.filter(user=request.user).first()
            if participant:
                return participant.unread_count
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            if other:
                return UserBasicSerializer(other).data
        return None


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation detail view."""
    participants = UserBasicSerializer(many=True, read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    participant_data = ConversationParticipantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'id', 'conversation_type', 'title', 'description',
            'participants', 'messages', 'participant_data',
            'related_car_id', 'related_part_id', 'related_order_id',
            'is_active', 'last_message_at', 'message_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversations."""
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=True
    )
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_type', 'title', 'description',
            'related_car_id', 'related_part_id', 'related_order_id',
            'participant_ids'
        ]
    
    def create(self, validated_data):
        participant_ids = validated_data.pop('participant_ids')
        conversation = Conversation.objects.create(**validated_data)
        
        # Add participants
        participants = CustomUser.objects.filter(id__in=participant_ids)
        conversation.participants.set(participants)
        
        return conversation


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """Serializer for typing indicators."""
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = TypingIndicator
        fields = ['id', 'conversation', 'user', 'is_typing', 'started_at', 'updated_at']
        read_only_fields = ['id', 'started_at', 'updated_at']


class BlockedUserSerializer(serializers.ModelSerializer):
    """Serializer for blocked users."""
    blocked_user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = BlockedUser
        fields = ['id', 'blocked_user', 'reason', 'blocked_at']
        read_only_fields = ['id', 'blocked_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages."""
    
    class Meta:
        model = Message
        fields = ['conversation', 'message_type', 'content', 'attachment', 'attachment_type']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['sender'] = request.user
        return super().create(validated_data)
