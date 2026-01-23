from django.test import TestCase
from django.contrib.auth import get_user_model
from notifications.models import Notification, NotificationPreference

User = get_user_model()


class NotificationModelTest(TestCase):
    """Test suite for Notification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            first_name="Test", last_name="User"
        )

    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type="new_message",
            title="New Message",
            message="You have a new message from seller"
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.notification_type, "new_message")
        self.assertEqual(notification.title, "New Message")

    def test_notification_defaults(self):
        """Test default values"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type="listing_update",
            title="Listing Update",
            message="Your listing has been viewed"
        )
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.created_at)

    def test_notification_types(self):
        """Test different notification types"""
        types = [
            "new_message",
            "listing_update",
            "expert_response",
            "review_received",
            "order_update"
        ]
        
        for ntype in types:
            Notification.objects.create(
                user=self.user,
                notification_type=ntype,
                title=f"{ntype} notification",
                message="Test message"
            )
        
        self.assertEqual(Notification.objects.filter(user=self.user).count(), len(types))

    def test_notification_with_action_url(self):
        """Test notification with action URL"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type="new_message",
            title="New Message",
            message="You have a new message",
            action_url="/messages/123"
        )
        self.assertEqual(notification.action_url, "/messages/123")

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.create(
            user=self.user,
            notification_type="review_received",
            title="New Review",
            message="You received a new review"
        )
        
        notification.is_read = True
        notification.save()
        
        self.assertTrue(notification.is_read)


class NotificationPreferenceModelTest(TestCase):
    """Test suite for NotificationPreference model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            first_name="Test", last_name="User"
        )

    def test_preference_creation(self):
        """Test creating notification preferences"""
        pref = NotificationPreference.objects.create(
            user=self.user,
            email_new_message=True,
            email_listing_update=False,
            app_new_message=True,
            app_listing_update=True,
            email_frequency="instant"
        )
        self.assertEqual(pref.user, self.user)
        self.assertTrue(pref.email_new_message)
        self.assertFalse(pref.email_listing_update)

    def test_preference_defaults(self):
        """Test default values"""
        pref = NotificationPreference.objects.create(user=self.user)
        
        # Most notifications should be enabled by default
        self.assertTrue(pref.app_new_message)
        self.assertEqual(pref.email_frequency, "instant")

    def test_preference_one_to_one(self):
        """Test one-to-one relationship"""
        NotificationPreference.objects.create(user=self.user)
        
        with self.assertRaises(Exception):
            NotificationPreference.objects.create(user=self.user)

    def test_email_frequency_options(self):
        """Test different email frequency options"""
        frequencies = ["instant", "daily", "weekly", "never"]
        
        for freq in frequencies:
            user = User.objects.create_user(
                email=f"user{freq}@example.com",
                password="pass123",
                first_name="User",
                last_name=freq
            )
            pref = NotificationPreference.objects.create(
                user=user,
                email_frequency=freq
            )
            self.assertEqual(pref.email_frequency, freq)

    def test_quiet_hours(self):
        """Test quiet hours functionality"""
        from datetime import time
        
        pref = NotificationPreference.objects.create(
            user=self.user,
            quiet_hours_enabled=True,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )
        
        self.assertTrue(pref.quiet_hours_enabled)
        self.assertEqual(pref.quiet_hours_start, time(22, 0))
