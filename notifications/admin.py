from django.contrib import admin
from notifications.models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'title', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__email']
    readonly_fields = ['id', 'created_at', 'read_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'email_frequency', 'quiet_hours_enabled']
    list_filter = ['email_frequency', 'quiet_hours_enabled']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
