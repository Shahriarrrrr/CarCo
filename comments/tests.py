from django.test import TestCase
from django.contrib.auth import get_user_model
from comments.models import Comment, CommentReply, CommentLike
from cars.models import Car
from parts.models import CarPart, PartCategory
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal

User = get_user_model()


class CommentModelTest(TestCase):
    """Test suite for Comment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="commenter@example.com",
            password="pass123",
            first_name="Commenter", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="Toyota",
            model="Camry",
            year=2020,
            price=Decimal("25000.00"),
            mileage=50000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used"
        )

    def test_comment_on_car(self):
        """Test creating a comment on a car"""
        comment = Comment.objects.create(
            author=self.user,
            content_object=self.car,
            text="Great car! Very interested."
        )
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.content_object, self.car)
        self.assertEqual(comment.text, "Great car! Very interested.")

    def test_comment_defaults(self):
        """Test default values"""
        comment = Comment.objects.create(
            author=self.user,
            content_object=self.car,
            text="Test comment"
        )
        self.assertEqual(comment.likes_count, 0)
        self.assertEqual(comment.replies_count, 0)
        self.assertTrue(comment.is_approved)
        self.assertFalse(comment.is_flagged)

    def test_comment_on_part(self):
        """Test creating a comment on a part"""
        category = PartCategory.objects.create(name="Parts")
        part = CarPart.objects.create(
            seller=self.seller,
            category=category,
            name="Brake Pads",
            price=Decimal("150.00"),
            quantity_in_stock=10,
            condition="new"
        )
        
        comment = Comment.objects.create(
            author=self.user,
            content_object=part,
            text="Do these fit 2020 Camry?"
        )
        self.assertEqual(comment.content_object, part)


class CommentReplyModelTest(TestCase):
    """Test suite for CommentReply model"""

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
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="Honda",
            model="Civic",
            year=2021,
            price=Decimal("22000.00"),
            mileage=30000,
            transmission="manual",
            fuel_type="petrol",
            condition="used"
        )
        self.comment = Comment.objects.create(
            author=self.user1,
            content_object=self.car,
            text="Is this still available?"
        )

    def test_reply_creation(self):
        """Test creating a reply to a comment"""
        reply = CommentReply.objects.create(
            comment=self.comment,
            author=self.seller,
            text="Yes, it's still available!"
        )
        self.assertEqual(reply.comment, self.comment)
        self.assertEqual(reply.author, self.seller)

    def test_reply_defaults(self):
        """Test default values"""
        reply = CommentReply.objects.create(
            comment=self.comment,
            author=self.user2,
            text="Great!"
        )
        self.assertEqual(reply.likes_count, 0)
        self.assertTrue(reply.is_approved)
        self.assertFalse(reply.is_flagged)

    def test_multiple_replies(self):
        """Test multiple replies on a comment"""
        CommentReply.objects.create(
            comment=self.comment,
            author=self.seller,
            text="Reply 1"
        )
        CommentReply.objects.create(
            comment=self.comment,
            author=self.user2,
            text="Reply 2"
        )
        
        self.assertEqual(self.comment.replies.count(), 2)


class CommentLikeModelTest(TestCase):
    """Test suite for CommentLike model"""

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
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="Ford",
            model="Mustang",
            year=2022,
            price=Decimal("45000.00"),
            mileage=10000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used"
        )
        self.comment = Comment.objects.create(
            author=self.user1,
            content_object=self.car,
            text="Amazing car!"
        )

    def test_like_comment(self):
        """Test liking a comment"""
        like = CommentLike.objects.create(
            user=self.user2,
            comment=self.comment
        )
        self.assertEqual(like.user, self.user2)
        self.assertEqual(like.comment, self.comment)

    def test_unique_like_per_user(self):
        """Test that a user can only like a comment once"""
        CommentLike.objects.create(
            user=self.user2,
            comment=self.comment
        )
        
        with self.assertRaises(Exception):
            CommentLike.objects.create(
                user=self.user2,
                comment=self.comment
            )

    def test_like_reply(self):
        """Test liking a reply"""
        reply = CommentReply.objects.create(
            comment=self.comment,
            author=self.seller,
            text="Thank you!"
        )
        
        like = CommentLike.objects.create(
            user=self.user1,
            reply=reply
        )
        self.assertEqual(like.reply, reply)

    def test_multiple_users_like_comment(self):
        """Test multiple users liking the same comment"""
        user3 = User.objects.create_user(
            email="user3@example.com",
            password="pass123",
            first_name="User", last_name="Three"
        )
        
        CommentLike.objects.create(user=self.user1, comment=self.comment)
        CommentLike.objects.create(user=self.user2, comment=self.comment)
        CommentLike.objects.create(user=user3, comment=self.comment)
        
        self.assertEqual(CommentLike.objects.filter(comment=self.comment).count(), 3)
