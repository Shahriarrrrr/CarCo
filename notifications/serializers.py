from rest_framework import serializers
from notifications.models import Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'is_read',
            'action_url', 'created_at', 'read_at'
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'message', 'created_at', 'read_at'
        ]


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    """Serializer for notification preferences."""
    
    class Meta:
        model = NotificationPreference
        fields = [
            'id', 'email_new_message', 'email_listing_update', 'email_expert_response',
            'email_review_received', 'email_seller_response', 'email_forum_reply',
            'email_part_available', 'email_price_alert', 'email_verification_status',
            'email_account_alert', 'email_system_announcement',
            'app_new_message', 'app_listing_update', 'app_expert_response',
            'app_review_received', 'app_seller_response', 'app_forum_reply',
            'app_part_available', 'app_price_alert', 'app_verification_status',
            'app_account_alert', 'app_system_announcement',
            'email_frequency', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end'
        ]
        read_only_fields = ['id']
