from django.db import models
from django.utils import timezone
import uuid
from users.models import CustomUser


class Conversation(models.Model):
    """
    Represents a conversation between two or more users.
    Can be one-on-one or group conversations.
    """
    
    CONVERSATION_TYPE_CHOICES = (
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('transaction', 'Transaction Related'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    
    # Conversation details
    conversation_type = models.CharField(
        max_length=20,
        choices=CONVERSATION_TYPE_CHOICES,
        default='direct',
        db_index=True
    )
    title = models.CharField(max_length=255, null=True, blank=True)  # For group chats
    description = models.TextField(null=True, blank=True)
    
    # Related transaction (optional)
    related_car_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_part_id = models.UUIDField(null=True, blank=True, db_index=True)
    related_order_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Conversation metadata
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(null=True, blank=True, db_index=True)
    message_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['conversation_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        if self.title:
            return self.title
        participant_names = ', '.join([p.get_full_name() for p in self.participants.all()[:3]])
        return f"Conversation: {participant_names}"
    
    def get_other_participant(self, user):
        """Get the other participant in a direct message conversation."""
        if self.conversation_type == 'direct':
            return self.participants.exclude(id=user.id).first()
        return None
    
    def add_participant(self, user):
        """Add a participant to the conversation."""
        if not self.participants.filter(id=user.id).exists():
            self.participants.add(user)
    
    def remove_participant(self, user):
        """Remove a participant from the conversation."""
        self.participants.remove(user)
    
    def update_last_message(self):
        """Update last message timestamp."""
        self.last_message_at = timezone.now()
        self.save(update_fields=['last_message_at'])


class Message(models.Model):
    """
    Individual message in a conversation.
    """
    
    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System Message'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField()
    
    # Attachments
    attachment = models.FileField(upload_to='messages/%Y/%m/%d/', null=True, blank=True)
    attachment_type = models.CharField(max_length=50, null=True, blank=True)  # image, pdf, etc.
    
    # Message status
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    # Read receipts
    read_by = models.ManyToManyField(CustomUser, related_name='read_messages', blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender']),
        ]
    
    def __str__(self):
        return f"Message from {self.sender.get_full_name()} in {self.conversation}"
    
    def mark_as_read(self, user):
        """Mark message as read by a user."""
        if not self.read_by.filter(id=user.id).exists():
            self.read_by.add(user)
    
    def get_read_count(self):
        """Get number of users who have read this message."""
        return self.read_by.count()
    
    def is_read_by_user(self, user):
        """Check if message is read by a specific user."""
        return self.read_by.filter(id=user.id).exists()


class MessageAttachment(models.Model):
    """
    Detailed information about message attachments.
    """
    
    ATTACHMENT_TYPE_CHOICES = (
        ('image', 'Image'),
        ('document', 'Document'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    
    # Attachment details
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()  # in bytes
    attachment_type = models.CharField(max_length=20, choices=ATTACHMENT_TYPE_CHOICES)
    mime_type = models.CharField(max_length=100)
    
    # Metadata
    width = models.IntegerField(null=True, blank=True)  # For images/videos
    height = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # For videos/audio in seconds
    
    # Timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['uploaded_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.attachment_type}"


class ConversationParticipant(models.Model):
    """
    Track participant-specific conversation metadata.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participant_data')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='conversation_participations')
    
    # Participant status
    is_muted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    
    # Read status
    last_read_message = models.ForeignKey(
        Message,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+'
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    unread_count = models.IntegerField(default=0)
    
    # Notifications
    notifications_enabled = models.BooleanField(default=True)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('conversation', 'user')
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} in {self.conversation}"
    
    def mark_as_read(self, message):
        """Mark conversation as read up to a specific message."""
        self.last_read_message = message
        self.last_read_at = timezone.now()
        self.unread_count = 0
        self.save()


class TypingIndicator(models.Model):
    """
    Track when users are typing in a conversation.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='typing_in')
    
    # Typing status
    is_typing = models.BooleanField(default=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('conversation', 'user')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} typing in {self.conversation}"
    
    def is_still_typing(self, timeout_seconds=5):
        """Check if user is still typing (within timeout)."""
        elapsed = (timezone.now() - self.updated_at).total_seconds()
        return elapsed < timeout_seconds


class BlockedUser(models.Model):
    """
    Track blocked users to prevent messaging.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blocker = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_users')
    blocked_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='blocked_by')
    
    # Block details
    reason = models.TextField(null=True, blank=True)
    
    # Timestamps
    blocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('blocker', 'blocked_user')
        ordering = ['-blocked_at']
    
    def __str__(self):
        return f"{self.blocker.get_full_name()} blocked {self.blocked_user.get_full_name()}"
