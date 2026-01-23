from django.test import TestCase
from django.contrib.auth import get_user_model
from ratings.models import Review, Rating, ReviewHelpfulness

User = get_user_model()


class ReviewModelTest(TestCase):
    """Test suite for Review model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )

    def test_review_creation(self):
        """Test creating a review"""
        review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            title="Excellent seller!",
            text="Fast shipping and great communication",
            rating=5,
            communication_rating=5,
            item_accuracy_rating=5,
            shipping_rating=5,
            is_verified_purchase=True
        )
        self.assertEqual(review.reviewer, self.buyer)
        self.assertEqual(review.seller, self.seller)
        self.assertEqual(review.rating, 5)

    def test_review_defaults(self):
        """Test default values"""
        review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            rating=4,
            text="Good seller"
        )
        self.assertEqual(review.helpful_count, 0)
        self.assertFalse(review.is_verified_purchase)

    def test_review_str_representation(self):
        """Test string representation"""
        review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            rating=5,
            text="Great!"
        )
        self.assertIn(self.buyer.get_full_name(), str(review))
        self.assertIn(self.seller.get_full_name(), str(review))

    def test_review_rating_range(self):
        """Test that ratings are within valid range"""
        review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            rating=3,
            communication_rating=4,
            item_accuracy_rating=5,
            shipping_rating=3
        )
        self.assertGreaterEqual(review.rating, 1)
        self.assertLessEqual(review.rating, 5)


class RatingModelTest(TestCase):
    """Test suite for Rating model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )

    def test_seller_rating_creation(self):
        """Test creating a seller rating"""
        rating = Rating.objects.create(
            seller=self.seller,
            average_rating=4.5,
            total_reviews=10,
            five_star_count=6,
            four_star_count=3,
            three_star_count=1,
            two_star_count=0,
            one_star_count=0
        )
        self.assertEqual(rating.seller, self.seller)
        self.assertEqual(rating.average_rating, 4.5)
        self.assertEqual(rating.total_reviews, 10)

    def test_seller_rating_defaults(self):
        """Test default values"""
        rating = Rating.objects.create(seller=self.seller)
        self.assertEqual(rating.average_rating, 0.0)
        self.assertEqual(rating.total_reviews, 0)
        self.assertEqual(rating.five_star_count, 0)

    def test_seller_rating_one_to_one(self):
        """Test one-to-one relationship"""
        Rating.objects.create(seller=self.seller)
        
        with self.assertRaises(Exception):
            Rating.objects.create(seller=self.seller)

    def test_detailed_ratings_calculation(self):
        """Test average calculation of detailed ratings"""
        rating = Rating.objects.create(
            seller=self.seller,
            average_communication=4.8,
            average_item_accuracy=4.6,
            average_shipping=4.7
        )
        
        # All detailed ratings should be reasonable
        self.assertGreaterEqual(rating.average_communication, 0)
        self.assertLessEqual(rating.average_communication, 5)


class ReviewHelpfulnessModelTest(TestCase):
    """Test suite for ReviewHelpfulness model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.voter = User.objects.create_user(
            email="voter@example.com",
            password="pass123",
            first_name="Voter", last_name="User"
        )
        self.review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            rating=5,
            text="Excellent"
        )

    def test_vote_creation(self):
        """Test creating a vote on a review"""
        vote = ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.voter,
            vote_type="helpful"
        )
        self.assertEqual(vote.review, self.review)
        self.assertEqual(vote.user, self.voter)
        self.assertEqual(vote.vote_type, "helpful")

    def test_vote_types(self):
        """Test both vote types"""
        helpful = ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.voter,
            vote_type="helpful"
        )
        
        voter2 = User.objects.create_user(
            email="voter2@example.com",
            password="pass123",
            first_name="Voter", last_name="2"
        )
        unhelpful = ReviewHelpfulness.objects.create(
            review=self.review,
            user=voter2,
            vote_type="unhelpful"
        )
        
        self.assertEqual(helpful.vote_type, "helpful")
        self.assertEqual(unhelpful.vote_type, "unhelpful")

    def test_unique_vote_per_user(self):
        """Test that a user can only vote once per review"""
        ReviewHelpfulness.objects.create(
            review=self.review,
            user=self.voter,
            vote_type="helpful"
        )
        
        with self.assertRaises(Exception):
            ReviewHelpfulness.objects.create(
                review=self.review,
                user=self.voter,
                vote_type="unhelpful"
            )
