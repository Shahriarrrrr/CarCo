from django.test import TestCase
from django.contrib.auth import get_user_model
from locations.models import ShopLocation
from parts.models import CompanyStore
from decimal import Decimal

User = get_user_model()


class ShopLocationModelTest(TestCase):
    """Test suite for ShopLocation model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Shop", last_name="Owner"
        )

    def test_location_creation(self):
        """Test creating a shop location"""
        location = ShopLocation.objects.create(
            seller=self.seller,
            name="AutoParts Center",
            location_type="shop",
            latitude=Decimal("23.8103"),
            longitude=Decimal("90.4125"),
            address="123 Main Street",
            city="Dhaka",
            state="Dhaka",
            country="Bangladesh",
            phone="+8801234567890",
            email="shop@example.com"
        )
        self.assertEqual(location.name, "AutoParts Center")
        self.assertEqual(location.seller, self.seller)
        self.assertEqual(location.location_type, "shop")

    def test_location_defaults(self):
        """Test default values"""
        location = ShopLocation.objects.create(
            seller=self.seller,
            name="Test Shop",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka"
        )
        self.assertEqual(location.approval_status, "pending")
        self.assertTrue(location.is_active)

    def test_location_str_representation(self):
        """Test string representation"""
        location = ShopLocation.objects.create(
            seller=self.seller,
            name="My Shop",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka"
        )
        self.assertIn("My Shop", str(location))

    def test_location_type_choices(self):
        """Test different location types"""
        shop = ShopLocation.objects.create(
            seller=self.seller,
            name="Shop",
            location_type="shop",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka"
        )
        service = ShopLocation.objects.create(
            seller=self.seller,
            name="Service Center",
            location_type="service",
            latitude=Decimal("23.1"),
            longitude=Decimal("90.1"),
            city="Dhaka"
        )
        warehouse = ShopLocation.objects.create(
            seller=self.seller,
            name="Warehouse",
            location_type="warehouse",
            latitude=Decimal("23.2"),
            longitude=Decimal("90.2"),
            city="Dhaka"
        )
        
        self.assertEqual(shop.location_type, "shop")
        self.assertEqual(service.location_type, "service")
        self.assertEqual(warehouse.location_type, "warehouse")

    def test_approval_status_choices(self):
        """Test approval status transitions"""
        location = ShopLocation.objects.create(
            seller=self.seller,
            name="Test Location",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka",
            approval_status="pending"
        )
        
        # Approve location
        location.approval_status = "approved"
        location.save()
        self.assertEqual(location.approval_status, "approved")
        
        # Reject location
        location.approval_status = "rejected"
        location.save()
        self.assertEqual(location.approval_status, "rejected")

    def test_operating_hours_json(self):
        """Test storing operating hours as JSON"""
        operating_hours = {
            "monday": "9:00 AM - 6:00 PM",
            "tuesday": "9:00 AM - 6:00 PM",
            "saturday": "10:00 AM - 4:00 PM",
            "sunday": "Closed"
        }
        
        location = ShopLocation.objects.create(
            seller=self.seller,
            name="Shop with Hours",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka",
            operating_hours=operating_hours
        )
        
        self.assertEqual(location.operating_hours["monday"], "9:00 AM - 6:00 PM")
        self.assertEqual(location.operating_hours["sunday"], "Closed")

    def test_location_with_company_store(self):
        """Test linking location to company store"""
        company_user = User.objects.create_user(
            email="company@example.com",
            password="pass123",
            first_name="Company", last_name="User",
            user_type="company"
        )
        
        store = CompanyStore.objects.create(
            company=company_user,
            store_name="AutoParts Inc"
        )
        
        location = ShopLocation.objects.create(
            seller=company_user,
            store=store,
            name="AutoParts Inc - Branch 1",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka"
        )
        
        self.assertEqual(location.store, store)

    def test_multiple_locations_per_seller(self):
        """Test that a seller can have multiple locations"""
        ShopLocation.objects.create(
            seller=self.seller,
            name="Location 1",
            latitude=Decimal("23.0"),
            longitude=Decimal("90.0"),
            city="Dhaka"
        )
        ShopLocation.objects.create(
            seller=self.seller,
            name="Location 2",
            latitude=Decimal("23.1"),
            longitude=Decimal("90.1"),
            city="Dhaka"
        )
        ShopLocation.objects.create(
            seller=self.seller,
            name="Location 3",
            latitude=Decimal("23.2"),
            longitude=Decimal("90.2"),
            city="Chittagong"
        )
        
        self.assertEqual(ShopLocation.objects.filter(seller=self.seller).count(), 3)
