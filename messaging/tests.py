from django.test import TestCase
from django.contrib.auth import get_user_model
from messaging.models import Conversation, Message, MessageAttachment, ConversationParticipant, BlockedUser

User = get_user_model()


class ConversationModelTest(TestCase):
    """Test suite for Conversation model"""

    def setUp(self):
        self.user1 = User.objects.create_user(
            email="user1@example.com",
            password="pass123",
            first_name="User", last_name="One"
        )
        self.user2 = User.objects.create_user(
            email="user2@example.com",
            password="pass123",
            first_name="User", last_name="Two"
        )

    def test_conversation_creation(self):
        """Test creating a conversation"""
        conversation = Conversation.objects.create(
            conversation_type="direct",
            title="Chat between users"
        )
        conversation.participants.add(self.user1, self.user2)
        
        self.assertEqual(conversation.participants.count(), 2)
        self.assertEqual(conversation.conversation_type, "direct")

    def test_conversation_defaults(self):
        """Test default values"""
        conversation = Conversation.objects.create()
        self.assertEqual(conversation.conversation_type, "direct")
        self.assertEqual(conversation.message_count, 0)

    def test_group_conversation(self):
        """Test creating a group conversation"""
        user3 = User.objects.create_user(
            email="user3@example.com",
            password="pass123",
            first_name="User", last_name="Three"
        )
        
        conversation = Conversation.objects.create(
            conversation_type="group",
            title="Group Chat"
        )
        conversation.participants.add(self.user1, self.user2, user3)
        
        self.assertEqual(conversation.participants.count(), 3)
        self.assertEqual(conversation.conversation_type, "group")


class MessageModelTest(TestCase):
    """Test suite for Message model"""

    def setUp(self):
        self.sender = User.objects.create_user(
            email="sender@example.com",
            password="pass123",
            first_name="Sender", last_name="User"
        )
        self.receiver = User.objects.create_user(
            email="receiver@example.com",
            password="pass123",
            first_name="Receiver", last_name="User"
        )
        self.conversation = Conversation.objects.create(
            conversation_type="direct"
        )
        self.conversation.participants.add(self.sender, self.receiver)

    def test_message_creation(self):
        """Test creating a message"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            message_type="text",
            content="Hello, how are you?"
        )
        self.assertEqual(message.content, "Hello, how are you?")
        self.assertEqual(message.sender, self.sender)

    def test_message_defaults(self):
        """Test default values"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            content="Test message"
        )
        self.assertEqual(message.message_type, "text")
        self.assertFalse(message.is_edited)

    def test_message_read_tracking(self):
        """Test read_by many-to-many relationship"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            content="Test"
        )
        message.read_by.add(self.receiver)
        
        self.assertEqual(message.read_by.count(), 1)
        self.assertIn(self.receiver, message.read_by.all())


class MessageAttachmentModelTest(TestCase):
    """Test suite for MessageAttachment model"""

    def setUp(self):
        self.sender = User.objects.create_user(
            email="sender@example.com",
            password="pass123",
            first_name="Sender", last_name="User"
        )
        self.conversation = Conversation.objects.create()
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            message_type="file",
            content="File attached"
        )

    def test_attachment_creation(self):
        """Test creating a message attachment"""
        attachment = MessageAttachment.objects.create(
            message=self.message,
            file_name="document.pdf",
            file_size=1024000,
            attachment_type="document",
            mime_type="application/pdf"
        )
        self.assertEqual(attachment.message, self.message)
        self.assertEqual(attachment.file_name, "document.pdf")

    def test_attachment_one_to_one(self):
        """Test multiple attachments allowed per message"""
        attachment1 = MessageAttachment.objects.create(
            message=self.message,
            file_name="file1.pdf",
            file_size=1024,
            attachment_type="document",
            mime_type="application/pdf"
        )
        
        # Multiple attachments should be allowed (ForeignKey relationship)
        attachment2 = MessageAttachment.objects.create(
            message=self.message,
            file_name="file2.pdf",
            file_size=2048,
            attachment_type="document",
            mime_type="application/pdf"
        )
        
        self.assertEqual(self.message.attachments.count(), 2)


class ConversationParticipantModelTest(TestCase):
    """Test suite for ConversationParticipant model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            first_name="User", last_name="User"
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user)

    def test_participant_metadata(self):
        """Test creating conversation participant metadata"""
        participant = ConversationParticipant.objects.create(
            conversation=self.conversation,
            user=self.user,
            is_muted=False,
            is_archived=False,
            unread_count=5
        )
        self.assertEqual(participant.unread_count, 5)
        self.assertFalse(participant.is_muted)

    def test_participant_defaults(self):
        """Test default values"""
        participant = ConversationParticipant.objects.create(
            conversation=self.conversation,
            user=self.user
        )
        self.assertFalse(participant.is_muted)
        self.assertFalse(participant.is_archived)
        self.assertFalse(participant.is_blocked)
        self.assertEqual(participant.unread_count, 0)


class BlockedUserModelTest(TestCase):
    """Test suite for BlockedUser model"""

    def setUp(self):
        self.blocker = User.objects.create_user(
            email="blocker@example.com",
            password="pass123",
            first_name="Blocker", last_name="User"
        )
        self.blocked = User.objects.create_user(
            email="blocked@example.com",
            password="pass123",
            first_name="Blocked", last_name="User"
        )

    def test_block_user(self):
        """Test blocking a user"""
        block = BlockedUser.objects.create(
            blocker=self.blocker,
            blocked_user=self.blocked
        )
        self.assertEqual(block.blocker, self.blocker)
        self.assertEqual(block.blocked_user, self.blocked)

    def test_unique_block(self):
        """Test that a user can only block another user once"""
        BlockedUser.objects.create(
            blocker=self.blocker,
            blocked_user=self.blocked
        )
        
        with self.assertRaises(Exception):
            BlockedUser.objects.create(
                blocker=self.blocker,
                blocked_user=self.blocked
            )
