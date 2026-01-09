from django.db import models
import uuid
from users.models import CustomUser


class Notification(models.Model):
    """
    System notifications for users.
    """
    
    NOTIFICATION_TYPE_CHOICES = (
        ('new_message', 'New Message'),
        ('listing_update', 'Listing Update'),
        ('expert_response', 'Expert Response'),
        ('review_received', 'Review Received'),
        ('seller_response', 'Seller Response'),
        ('forum_reply', 'Forum Reply'),
        ('part_available', 'Part Available'),
        ('price_alert', 'Price Alert'),
        ('verification_status', 'Verification Status'),
        ('account_alert', 'Account Alert'),
        ('system_announcement', 'System Announcement'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    
    # Notification content
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related object (optional)
    related_object_id = models.UUIDField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False, db_index=True)
    
    # Action URL
    action_url = models.CharField(max_length=500, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.get_full_name()}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class NotificationPreference(models.Model):
    """
    User notification preferences.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notifications
    email_new_message = models.BooleanField(default=True)
    email_listing_update = models.BooleanField(default=True)
    email_expert_response = models.BooleanField(default=True)
    email_review_received = models.BooleanField(default=True)
    email_seller_response = models.BooleanField(default=True)
    email_forum_reply = models.BooleanField(default=True)
    email_part_available = models.BooleanField(default=True)
    email_price_alert = models.BooleanField(default=True)
    email_verification_status = models.BooleanField(default=True)
    email_account_alert = models.BooleanField(default=True)
    email_system_announcement = models.BooleanField(default=False)
    
    # In-app notifications
    app_new_message = models.BooleanField(default=True)
    app_listing_update = models.BooleanField(default=True)
    app_expert_response = models.BooleanField(default=True)
    app_review_received = models.BooleanField(default=True)
    app_seller_response = models.BooleanField(default=True)
    app_forum_reply = models.BooleanField(default=True)
    app_part_available = models.BooleanField(default=True)
    app_price_alert = models.BooleanField(default=True)
    app_verification_status = models.BooleanField(default=True)
    app_account_alert = models.BooleanField(default=True)
    app_system_announcement = models.BooleanField(default=True)
    
    # Notification frequency
    FREQUENCY_CHOICES = (
        ('instant', 'Instant'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
    )
    
    email_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='instant')
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Notification Preferences"
    
    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name()}"
