from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
from users.models import CustomUser


class Comment(models.Model):
    """
    Generic comment model for cars and car parts.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comments')
    
    # Generic relation to Car or CarPart
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Content
    text = models.TextField()
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    replies_count = models.IntegerField(default=0)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.get_full_name()}"


class CommentReply(models.Model):
    """
    Nested replies to comments.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comment_replies')
    
    # Content
    text = models.TextField()
    
    # Engagement
    likes_count = models.IntegerField(default=0)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['comment']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Reply by {self.author.get_full_name()}"


class CommentLike(models.Model):
    """
    Track likes on comments and replies.
    """
    
    LIKE_TYPE_CHOICES = (
        ('comment', 'Comment'),
        ('reply', 'Reply'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='comment_likes')
    
    # Generic relation to Comment or CommentReply
    like_type = models.CharField(max_length=20, choices=LIKE_TYPE_CHOICES)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    reply = models.ForeignKey(CommentReply, on_delete=models.CASCADE, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [
            ('user', 'comment'),
            ('user', 'reply'),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Like by {self.user.get_full_name()}"
