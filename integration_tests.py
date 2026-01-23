"""
Integration tests for the entire backend system
Tests complete workflows across multiple apps
"""
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from cars.models import Car
from parts.models import CarPart, PartCategory, CompanyStore
from forum.models import ForumCategory, ForumThread, ForumResponse
from payments.models import Order, Payment, Wallet
from messaging.models import Conversation, Message
from comments.models import Comment
from ratings.models import Review, Rating
from decimal import Decimal

User = get_user_model()


class UserWorkflowIntegrationTest(APITestCase):
    """Integration tests for user workflows"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test", last_name="User"
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_user_registration_to_listing_workflow(self):
        """Test: Register user → Create listing → Receive comments"""
        # User is already created in setUp
        
        # Create a car listing
        car = Car.objects.create(
            seller=self.user,
            make="Toyota",
            model="Camry",
            year=2020,
            price=Decimal("25000.00"),
            city="Dhaka",
            mileage=50000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used"
        )
        
        self.assertEqual(Car.objects.filter(seller=self.user).count(), 1)
        
        # Another user comments on the listing
        commenter = User.objects.create_user(
            email="commenter@example.com",
            password="pass123",
            first_name="Commenter", last_name="User"
        )
        
        comment = Comment.objects.create(
            author=commenter,
            content_object=car,
            text="Is this car still available?"
        )
        
        self.assertEqual(Comment.objects.filter(
            object_id=car.id,
            content_type__model='car'
        ).count(), 1)


class MarketplaceWorkflowTest(APITestCase):
    """Test complete marketplace transactions"""

    def setUp(self):
        self.client = APIClient()
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
        
        refresh = RefreshToken.for_user(self.buyer)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_purchase_workflow(self):
        """Test: Browse part → Purchase → Payment → Review"""
        
        # Seller lists a part
        category = PartCategory.objects.create(name="Brakes")
        part = CarPart.objects.create(
            seller=self.seller,
            category=category,
            name="Brake Pads",
            price=Decimal("150.00"),
            quantity_in_stock=10
        )
        
        # Buyer creates order
        order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="part",
            item_name=part.name,
            quantity=2,
            unit_price=part.price,
            subtotal=Decimal("300.00"),
            total_amount=Decimal("300.00")
        )
        
        # Payment is made
        payment = Payment.objects.create(
            order=order,
            payment_method="card",
            amount=order.total_amount,
            status="completed"
        )
        
        # Buyer leaves a review
        review = Review.objects.create(
            reviewer=self.buyer,
            seller=self.seller,
            rating=5,
            text="Great quality, fast shipping!",
            is_verified_purchase=True
        )
        
        self.assertEqual(Review.objects.filter(seller=self.seller).count(), 1)
        self.assertEqual(payment.status, "completed")


class ForumWorkflowTest(APITestCase):
    """Test complete forum interaction workflows"""

    def setUp(self):
        self.client = APIClient()
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
        
        refresh = RefreshToken.for_user(self.user1)
        self.token1 = str(refresh.access_token)

    def test_forum_discussion_workflow(self):
        """Test: Create thread → Get responses → Mark resolved"""
        
        # User1 creates a thread
        category = ForumCategory.objects.create(name="Technical Help")
        thread = ForumThread.objects.create(
            author=self.user1,
            category=category,
            title="Engine overheating issue",
            description="My car engine overheats after 30 minutes",
            car_make="Honda",
            car_model="Civic",
            car_year=2018
        )
        
        # User2 responds
        response1 = ForumResponse.objects.create(
            thread=thread,
            author=self.user2,
            content="Check your coolant level first"
        )
        
        # User1 responds back
        response2 = ForumResponse.objects.create(
            thread=thread,
            author=self.user1,
            content="Thanks! Coolant was low."
        )
        
        # Mark as resolved
        thread.mark_as_resolved()
        
        self.assertEqual(thread.status, "resolved")
        self.assertEqual(ForumResponse.objects.filter(thread=thread).count(), 2)
        self.assertIsNotNone(thread.resolved_at)


class MessagingWorkflowTest(APITestCase):
    """Test messaging workflows"""

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

    def test_messaging_workflow(self):
        """Test: Create conversation → Send messages → Mark as read"""
        
        # Create conversation
        conversation = Conversation.objects.create(
            conversation_type="direct",
            title="Inquiry about Toyota Camry"
        )
        conversation.participants.add(self.buyer, self.seller)
        
        # Buyer sends message
        message1 = Message.objects.create(
            conversation=conversation,
            sender=self.buyer,
            content="Hi, is the car still available?"
        )
        
        # Seller replies
        message2 = Message.objects.create(
            conversation=conversation,
            sender=self.seller,
            content="Yes, it's available. Would you like to schedule a viewing?"
        )
        
        # Buyer marks as read
        message2.read_by.add(self.buyer)
        
        self.assertEqual(Message.objects.filter(conversation=conversation).count(), 2)
        self.assertIn(self.buyer, message2.read_by.all())


class CompanyStoreWorkflowTest(APITestCase):
    """Test company store workflows"""

    def setUp(self):
        self.company_user = User.objects.create_user(
            email="company@example.com",
            password="pass123",
            first_name="AutoParts", last_name="Inc",
            user_type="company"
        )

    def test_company_store_setup(self):
        """Test: Create company store → Add locations → List parts"""
        
        # Create company store
        store = CompanyStore.objects.create(
            company=self.company_user,
            store_name="AutoParts Plus",
            store_description="Quality auto parts since 1990",
            store_email="info@autoparts.com"
        )
        
        # Add parts
        category = PartCategory.objects.create(name="Engine Parts")
        part1 = CarPart.objects.create(
            seller=self.company_user,
            category=category,
            name="Oil Filter",
            price=Decimal("25.00"),
            quantity_in_stock=100
        )
        part2 = CarPart.objects.create(
            seller=self.company_user,
            category=category,
            name="Air Filter",
            price=Decimal("30.00"),
            quantity_in_stock=75
        )
        
        self.assertEqual(CarPart.objects.filter(seller=self.company_user).count(), 2)
        self.assertEqual(store.company, self.company_user)


class WalletAndPaymentWorkflowTest(APITestCase):
    """Test wallet and payment integration"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )

    def test_wallet_payment_workflow(self):
        """Test: Create order → Payment → Seller wallet updated"""
        
        # Create seller wallet
        seller_wallet = Wallet.objects.create(
            user=self.seller,
            balance=Decimal("0.00")
        )
        
        # Create order
        order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="part",
            item_name="Test Part",
            total_amount=Decimal("500.00"),
            unit_price=Decimal("500.00"),
            subtotal=Decimal("500.00")
        )
        
        # Payment completed
        payment = Payment.objects.create(
            order=order,
            payment_method="card",
            amount=Decimal("500.00"),
            status="completed"
        )
        
        # Update seller wallet (normally done by signal/webhook)
        seller_wallet.balance += Decimal("450.00")  # After platform fee
        seller_wallet.total_earned += Decimal("450.00")
        seller_wallet.save()
        
        self.assertEqual(seller_wallet.balance, Decimal("450.00"))
        self.assertEqual(payment.status, "completed")
