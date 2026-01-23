from django.test import TestCase
from django.contrib.auth import get_user_model
from parts.models import (
    PartCategory, CompanyStore, CarPart, PartImage, 
    PartCompatibility, PartReview, PartReviewHelpfulness
)
from decimal import Decimal

User = get_user_model()


class PartCategoryModelTest(TestCase):
    """Test suite for PartCategory model"""

    def setUp(self):
        self.parent_category = PartCategory.objects.create(
            name="Engine Parts",
            description="All engine related parts"
        )

    def test_category_creation(self):
        """Test creating a part category"""
        self.assertEqual(self.parent_category.name, "Engine Parts")
        self.assertIsNotNone(self.parent_category.id)

    def test_nested_category(self):
        """Test creating a nested category"""
        sub_category = PartCategory.objects.create(
            name="Oil Filters",
            description="Engine oil filters",
            parent_category=self.parent_category
        )
        self.assertEqual(sub_category.parent_category, self.parent_category)


class CompanyStoreModelTest(TestCase):
    """Test suite for CompanyStore model"""

    def setUp(self):
        self.company_user = User.objects.create_user(
            email="company@example.com",
            password="pass123",
            first_name="Auto", last_name="Parts Co",
            user_type="company"
        )

    def test_store_creation(self):
        """Test creating a company store"""
        store = CompanyStore.objects.create(
            company=self.company_user,
            store_name="AutoParts Plus",
            store_description="Quality auto parts",
            store_email="info@autoparts.com",
            store_phone="+8801234567890"
        )
        self.assertEqual(store.company, self.company_user)
        self.assertEqual(store.store_name, "AutoParts Plus")

    def test_store_one_to_one(self):
        """Test one-to-one relationship"""
        CompanyStore.objects.create(
            company=self.company_user,
            store_name="Store 1"
        )
        
        with self.assertRaises(Exception):
            CompanyStore.objects.create(
                company=self.company_user,
                store_name="Store 2"
            )


class CarPartModelTest(TestCase):
    """Test suite for CarPart model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="partseller@example.com",
            password="pass123",
            first_name="Part", last_name="Seller"
        )
        self.category = PartCategory.objects.create(
            name="Brakes",
            description="Brake parts"
        )
        self.part = CarPart.objects.create(
            seller=self.seller,
            category=self.category,
            name="Brake Pads - Front",
            description="High quality brake pads",
            part_number="BP-12345",
            condition="new",
            brand="Brembo",
            price=Decimal("150.00"),
            quantity_in_stock=50,
            status="available"
        )

    def test_part_creation(self):
        """Test creating a car part"""
        self.assertEqual(self.part.name, "Brake Pads - Front")
        self.assertEqual(self.part.seller, self.seller)
        self.assertEqual(self.part.price, Decimal("150.00"))
        self.assertEqual(self.part.quantity_in_stock, 50)

    def test_part_str_representation(self):
        """Test string representation"""
        self.assertIn(self.part.name, str(self.part))

    def test_part_defaults(self):
        """Test default values"""
        part = CarPart.objects.create(
            seller=self.seller,
            category=self.category,
            name="Oil Filter",
            price=Decimal("25.00"),
            quantity_in_stock=10,
            condition="new"
        )
        self.assertEqual(part.condition, "new")
        self.assertEqual(part.status, "pending")
        self.assertEqual(part.quantity_in_stock, 10)
        self.assertEqual(part.rating, Decimal("0.00"))


class PartCompatibilityModelTest(TestCase):
    """Test suite for PartCompatibility model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.category = PartCategory.objects.create(name="Parts")
        self.part = CarPart.objects.create(
            seller=self.seller,
            category=self.category,
            name="Air Filter",
            price=Decimal("30.00"),
            quantity_in_stock=20
        )

    def test_compatibility_creation(self):
        """Test creating part compatibility"""
        compat = PartCompatibility.objects.create(
            part=self.part,
            car_make="Toyota",
            car_model="Camry",
            car_year_from=2015,
            car_year_to=2020
        )
        self.assertEqual(compat.part, self.part)
        self.assertEqual(compat.car_make, "Toyota")
        self.assertEqual(compat.car_year_from, 2015)

    def test_multiple_compatibilities(self):
        """Test that a part can have multiple compatibilities"""
        PartCompatibility.objects.create(
            part=self.part,
            car_make="Toyota",
            car_model="Camry",
            car_year_from=2015,
            car_year_to=2020
        )
        PartCompatibility.objects.create(
            part=self.part,
            car_make="Honda",
            car_model="Accord",
            car_year_from=2016,
            car_year_to=2021
        )
        
        self.assertEqual(self.part.compatibilities.count(), 2)


class PartReviewModelTest(TestCase):
    """Test suite for PartReview model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.reviewer = User.objects.create_user(
            email="reviewer@example.com",
            password="pass123",
            first_name="Reviewer", last_name="User"
        )
        self.category = PartCategory.objects.create(name="Parts")
        self.part = CarPart.objects.create(
            seller=self.seller,
            category=self.category,
            name="Spark Plugs",
            price=Decimal("50.00"),
            quantity_in_stock=100
        )

    def test_review_creation(self):
        """Test creating a part review"""
        review = PartReview.objects.create(
            part=self.part,
            reviewer=self.reviewer,
            title="Great product!",
            text="These spark plugs work perfectly",
            rating=5,
            quality_rating=5,
            value_rating=4,
            fitment_rating=5
        )
        self.assertEqual(review.part, self.part)
        self.assertEqual(review.reviewer, self.reviewer)
        self.assertEqual(review.rating, 5)

    def test_review_defaults(self):
        """Test default values"""
        review = PartReview.objects.create(
            part=self.part,
            reviewer=self.reviewer,
            rating=4,
            text="Good part"
        )
        self.assertEqual(review.helpful_count, 0)
        self.assertFalse(review.is_verified_purchase)

    def test_multiple_reviews_per_part(self):
        """Test that a part can have multiple reviews"""
        PartReview.objects.create(
            part=self.part,
            reviewer=self.reviewer,
            rating=5,
            text="Excellent"
        )
        
        reviewer2 = User.objects.create_user(
            email="reviewer2@example.com",
            password="pass123",
            first_name="Reviewer2", last_name="User"
        )
        PartReview.objects.create(
            part=self.part,
            reviewer=reviewer2,
            rating=4,
            text="Good"
        )
        
        self.assertEqual(self.part.reviews.count(), 2)


class PartReviewHelpfulnessModelTest(TestCase):
    """Test suite for PartReviewHelpfulness model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.reviewer = User.objects.create_user(
            email="reviewer@example.com",
            password="pass123",
            first_name="Reviewer", last_name="User"
        )
        self.voter = User.objects.create_user(
            email="voter@example.com",
            password="pass123",
            first_name="Voter", last_name="User"
        )
        self.category = PartCategory.objects.create(name="Parts")
        self.part = CarPart.objects.create(
            seller=self.seller,
            category=self.category,
            name="Test Part",
            price=Decimal("100.00"),
            quantity_in_stock=50
        )
        self.review = PartReview.objects.create(
            part=self.part,
            reviewer=self.reviewer,
            rating=5,
            text="Great"
        )

    def test_vote_creation(self):
        """Test creating a review vote"""
        vote = PartReviewHelpfulness.objects.create(
            review=self.review,
            user=self.voter,
            vote_type="helpful"
        )
        self.assertEqual(vote.review, self.review)
        self.assertEqual(vote.user, self.voter)
        self.assertEqual(vote.vote_type, "helpful")

    def test_unique_vote_per_user(self):
        """Test that a user can only vote once per review"""
        PartReviewHelpfulness.objects.create(
            review=self.review,
            user=self.voter,
            vote_type="helpful"
        )
        
        with self.assertRaises(Exception):
            PartReviewHelpfulness.objects.create(
                review=self.review,
                user=self.voter,
                vote_type="unhelpful"
            )
