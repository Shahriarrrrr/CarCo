from django.test import TestCase
from django.contrib.auth import get_user_model
from forum.models import ForumCategory, ForumThread, ForumResponse, ExpertVerification, ResponseVote
from django.utils import timezone

User = get_user_model()


class ForumCategoryModelTest(TestCase):
    """Test suite for ForumCategory model"""

    def setUp(self):
        self.category = ForumCategory.objects.create(
            name="General Discussion",
            description="General automotive discussions"
        )

    def test_category_creation(self):
        """Test that a category can be created with valid data"""
        self.assertEqual(self.category.name, "General Discussion")
        self.assertIsNotNone(self.category.id)
        self.assertTrue(isinstance(self.category, ForumCategory))

    def test_category_str_representation(self):
        """Test the string representation of ForumCategory"""
        self.assertEqual(str(self.category), "General Discussion")

    def test_category_is_active_default(self):
        """Test that is_active defaults to True"""
        self.assertTrue(self.category.is_active)

    def test_category_unique_name(self):
        """Test that category names must be unique"""
        with self.assertRaises(Exception):
            ForumCategory.objects.create(
                name="General Discussion",
                description="Duplicate"
            )


class ForumThreadModelTest(TestCase):
    """Test suite for ForumThread model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test", last_name="User"
        )
        self.category = ForumCategory.objects.create(
            name="Technical Help",
            description="Get technical help"
        )
        self.thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Engine problem help",
            description="My engine makes a strange noise",
            car_make="Toyota",
            car_model="Camry",
            car_year=2015,
            status="open"
        )

    def test_thread_creation(self):
        """Test that a thread can be created successfully"""
        self.assertEqual(self.thread.title, "Engine problem help")
        self.assertEqual(self.thread.author, self.user)
        self.assertEqual(self.thread.category, self.category)
        self.assertEqual(self.thread.status, "open")

    def test_thread_str_representation(self):
        """Test the string representation of ForumThread"""
        self.assertEqual(str(self.thread), "Engine problem help")

    def test_thread_defaults(self):
        """Test default values for thread fields"""
        thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Test Thread",
            description="Test description"
        )
        self.assertEqual(thread.views_count, 0)
        self.assertEqual(thread.responses_count, 0)
        self.assertEqual(thread.status, "open")
        self.assertIsNotNone(thread.created_at)
        self.assertFalse(thread.is_pinned)
        self.assertFalse(thread.is_featured)

    def test_thread_car_info_optional(self):
        """Test that car information fields are optional"""
        thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="General Question",
            description="General question"
        )
        self.assertIsNone(thread.car_make)
        self.assertIsNone(thread.car_model)
        self.assertIsNone(thread.car_year)

    def test_mark_as_resolved(self):
        """Test marking thread as resolved"""
        self.thread.mark_as_resolved()
        self.assertEqual(self.thread.status, "resolved")
        self.assertIsNotNone(self.thread.resolved_at)


class ForumResponseModelTest(TestCase):
    """Test suite for ForumResponse model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="responder@example.com",
            password="pass123",
            first_name="Response", last_name="User"
        )
        self.category = ForumCategory.objects.create(
            name="Help",
            description="Help category"
        )
        self.thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Need help",
            description="Need help with something"
        )
        self.response = ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Here's my suggestion..."
        )

    def test_response_creation(self):
        """Test that a response can be created"""
        self.assertEqual(self.response.content, "Here's my suggestion...")
        self.assertEqual(self.response.thread, self.thread)
        self.assertEqual(self.response.author, self.user)

    def test_response_str_representation(self):
        """Test the string representation of ForumResponse"""
        expected = f"Response by {self.user.get_full_name()} on {self.thread.title}"
        self.assertEqual(str(self.response), expected)

    def test_response_defaults(self):
        """Test default values for response fields"""
        self.assertEqual(self.response.helpful_count, 0)
        self.assertEqual(self.response.unhelpful_count, 0)
        self.assertTrue(self.response.is_approved)
        self.assertFalse(self.response.is_flagged)
        self.assertFalse(self.response.is_expert_response)
        self.assertFalse(self.response.is_ai_response)

    def test_helpfulness_score(self):
        """Test get_helpfulness_score method"""
        self.response.helpful_count = 8
        self.response.unhelpful_count = 2
        self.response.save()
        score = self.response.get_helpfulness_score()
        self.assertEqual(score, 80.0)

    def test_helpfulness_score_no_votes(self):
        """Test helpfulness score when no votes"""
        score = self.response.get_helpfulness_score()
        self.assertEqual(score, 0)

    def test_response_cascade_delete(self):
        """Test that responses are deleted when thread is deleted"""
        thread_id = self.thread.id
        self.thread.delete()
        self.assertEqual(ForumResponse.objects.filter(thread_id=thread_id).count(), 0)


class ExpertVerificationModelTest(TestCase):
    """Test suite for ExpertVerification model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="expert@example.com",
            password="pass123",
            first_name="Expert", last_name="User"
        )
        self.verification = ExpertVerification.objects.create(
            user=self.user,
            expertise_areas=["Engine Repair", "Electrical Systems"],
            years_of_experience=10,
            bio="Experienced mechanic"
        )

    def test_expert_verification_creation(self):
        """Test creating expert verification"""
        self.assertEqual(self.verification.user, self.user)
        self.assertEqual(self.verification.years_of_experience, 10)
        self.assertEqual(self.verification.status, "pending")

    def test_expert_str_representation(self):
        """Test string representation"""
        expected = f"{self.user.get_full_name()} - Expert"
        self.assertEqual(str(self.verification), expected)

    def test_get_helpfulness_rate(self):
        """Test helpfulness rate calculation"""
        self.verification.total_responses = 10
        self.verification.helpful_responses = 8
        self.verification.save()
        rate = self.verification.get_helpfulness_rate()
        self.assertEqual(rate, 80.0)

    def test_helpfulness_rate_no_responses(self):
        """Test helpfulness rate with no responses"""
        rate = self.verification.get_helpfulness_rate()
        self.assertEqual(rate, 0)


class ResponseVoteModelTest(TestCase):
    """Test suite for ResponseVote model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="voter@example.com",
            password="pass123",
            first_name="Voter", last_name="User"
        )
        self.category = ForumCategory.objects.create(name="Test")
        self.thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Test",
            description="Test"
        )
        self.response = ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test response"
        )

    def test_vote_creation(self):
        """Test creating a vote"""
        vote = ResponseVote.objects.create(
            response=self.response,
            user=self.user,
            vote_type="helpful"
        )
        self.assertEqual(vote.vote_type, "helpful")
        self.assertEqual(vote.response, self.response)
        self.assertEqual(vote.user, self.user)

    def test_vote_str_representation(self):
        """Test vote string representation"""
        vote = ResponseVote.objects.create(
            response=self.response,
            user=self.user,
            vote_type="helpful"
        )
        expected = f"{self.user.get_full_name()} - helpful on response"
        self.assertEqual(str(vote), expected)

    def test_unique_vote_per_user_response(self):
        """Test that a user can only vote once per response"""
        ResponseVote.objects.create(
            response=self.response,
            user=self.user,
            vote_type="helpful"
        )
        with self.assertRaises(Exception):
            ResponseVote.objects.create(
                response=self.response,
                user=self.user,
                vote_type="unhelpful"
            )
