from django.test import TestCase
from django.contrib.auth import get_user_model
from cars.models import Car, CarImage, CarSpecification
from decimal import Decimal

User = get_user_model()


class CarModelTest(TestCase):
    """Test suite for Car model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Car", last_name="Seller"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="Toyota",
            model="Camry",
            year=2020,
            mileage=15000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used",
            price=Decimal("25000.00"),
            title="2020 Toyota Camry - Excellent Condition",
            description="Well-maintained car",
            city="Dhaka",
            state_province="Dhaka",
            country="Bangladesh",
            status="active"
        )

    def test_car_creation(self):
        """Test creating a car listing"""
        self.assertEqual(self.car.make, "Toyota")
        self.assertEqual(self.car.model, "Camry")
        self.assertEqual(self.car.year, 2020)
        self.assertEqual(self.car.price, Decimal("25000.00"))
        self.assertEqual(self.car.seller, self.seller)

    def test_car_str_representation(self):
        """Test string representation"""
        expected = f"{self.car.year} {self.car.make} {self.car.model}"
        self.assertIn(self.car.make, str(self.car))
        self.assertIn(self.car.model, str(self.car))

    def test_car_defaults(self):
        """Test default values"""
        car = Car.objects.create(
            seller=self.seller,
            make="Honda",
            model="Civic",
            year=2019,
            mileage=10000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used",
            price=Decimal("20000.00")
        )
        self.assertEqual(car.status, "pending")
        self.assertIsNotNone(car.created_at)

    def test_car_status_choices(self):
        """Test that status can be set to different values"""
        self.car.status = "sold"
        self.car.save()
        self.assertEqual(self.car.status, "sold")


class CarImageModelTest(TestCase):
    """Test suite for CarImage model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="Toyota",
            model="Corolla",
            year=2021,
            mileage=5000,
            transmission="automatic",
            fuel_type="petrol",
            condition="used",
            price=Decimal("22000.00")
        )

    def test_car_image_creation(self):
        """Test creating a car image"""
        image = CarImage.objects.create(
            car=self.car,
            is_primary=True
        )
        self.assertEqual(image.car, self.car)
        self.assertTrue(image.is_primary)

    def test_multiple_images_per_car(self):
        """Test that a car can have multiple images"""
        CarImage.objects.create(car=self.car, is_primary=True)
        CarImage.objects.create(car=self.car, is_primary=False)
        CarImage.objects.create(car=self.car, is_primary=False)
        
        self.assertEqual(self.car.images.count(), 3)

    def test_image_cascade_delete(self):
        """Test that images are deleted when car is deleted"""
        CarImage.objects.create(car=self.car)
        car_id = self.car.id
        self.car.delete()
        
        self.assertEqual(CarImage.objects.filter(car_id=car_id).count(), 0)


class CarSpecificationModelTest(TestCase):
    """Test suite for CarSpecification model"""

    def setUp(self):
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.car = Car.objects.create(
            seller=self.seller,
            make="BMW",
            model="M3",
            year=2022,
            mileage=3000,
            transmission="automatic",
            fuel_type="petrol",
            condition="new",
            price=Decimal("60000.00")
        )

    def test_specification_creation(self):
        """Test creating car specifications"""
        spec = CarSpecification.objects.create(
            car=self.car,
            horsepower=473,
            torque=550,
            acceleration_0_100=3.9,
            top_speed=290,
            fuel_consumption_city=10.2
        )
        self.assertEqual(spec.car, self.car)
        self.assertEqual(spec.horsepower, 473)
        self.assertEqual(spec.top_speed, 290)

    def test_specification_one_to_one(self):
        """Test that specification has one-to-one relationship with car"""
        CarSpecification.objects.create(
            car=self.car,
            horsepower=400
        )
        
        # Attempting to create another spec for same car should fail
        with self.assertRaises(Exception):
            CarSpecification.objects.create(
                car=self.car,
                horsepower=500
            )

    def test_specification_cascade_delete(self):
        """Test that specification is deleted when car is deleted"""
        spec = CarSpecification.objects.create(car=self.car, horsepower=400)
        car_id = self.car.id
        self.car.delete()
        
        self.assertEqual(CarSpecification.objects.filter(car_id=car_id).count(), 0)
