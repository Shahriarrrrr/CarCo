from django.contrib import admin
from messaging.models import (
    Conversation, Message, MessageAttachment, ConversationParticipant,
    TypingIndicator, BlockedUser
)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation_type', 'title', 'is_active', 'message_count', 'last_message_at', 'created_at']
    list_filter = ['conversation_type', 'is_active', 'created_at']
    search_fields = ['title', 'participants__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['participants']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'message_type', 'created_at']
    list_filter = ['message_type', 'created_at']
    search_fields = ['content', 'sender__email', 'conversation__title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'file_name', 'attachment_type', 'file_size', 'uploaded_at']
    list_filter = ['attachment_type', 'uploaded_at']
    search_fields = ['file_name', 'message__content']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'is_muted', 'is_archived', 'unread_count', 'joined_at']
    list_filter = ['is_muted', 'is_archived', 'joined_at']
    search_fields = ['user__email', 'conversation__title']
    readonly_fields = ['id', 'joined_at']


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'is_typing', 'updated_at']
    list_filter = ['is_typing', 'updated_at']
    search_fields = ['user__email', 'conversation__title']
    readonly_fields = ['id', 'started_at', 'updated_at']


@admin.register(BlockedUser)
class BlockedUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'blocker', 'blocked_user', 'blocked_at']
    list_filter = ['blocked_at']
    search_fields = ['blocker__email', 'blocked_user__email']
    readonly_fields = ['id', 'blocked_at']
