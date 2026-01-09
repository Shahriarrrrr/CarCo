from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from users.models import CustomUser


class Car(models.Model):
    """
    Car listing model for buying and selling vehicles.
    """
    
    CONDITION_CHOICES = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    )
    
    TRANSMISSION_CHOICES = (
        ('manual', 'Manual'),
        ('automatic', 'Automatic'),
        ('cvt', 'CVT'),
    )
    
    FUEL_TYPE_CHOICES = (
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric'),
        ('lpg', 'LPG'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('sold', 'Sold'),
        ('archived', 'Archived'),
        ('pending', 'Pending Review'),
    )
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='cars_for_sale')
    
    # Basic information
    make = models.CharField(max_length=100, db_index=True)  # e.g., Toyota
    model = models.CharField(max_length=100, db_index=True)  # e.g., Camry
    year = models.IntegerField(
        validators=[
            MinValueValidator(1900),
            MaxValueValidator(timezone.now().year + 1)
        ],
        db_index=True
    )
    
    # Specifications
    mileage = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Mileage in kilometers"
    )
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES)
    fuel_type = models.CharField(max_length=20, choices=FUEL_TYPE_CHOICES)
    engine_capacity = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Engine capacity in liters"
    )
    
    # Condition and pricing
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    # Description
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Location
    city = models.CharField(max_length=100, db_index=True)
    state_province = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    
    # Status and management
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    sold_at = models.DateTimeField(null=True, blank=True)
    
    # Additional features
    color = models.CharField(max_length=50, null=True, blank=True)
    body_type = models.CharField(max_length=50, null=True, blank=True)  # Sedan, SUV, etc.
    doors = models.IntegerField(null=True, blank=True)
    seats = models.IntegerField(null=True, blank=True)
    
    # Features (JSON field for flexibility)
    features = models.JSONField(
        default=list,
        blank=True,
        help_text="List of features: ['AC', 'Power Steering', 'ABS', etc.]"
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['make', 'model', 'year']),
            models.Index(fields=['price']),
            models.Index(fields=['city']),
        ]
    
    def __str__(self):
        return f"{self.year} {self.make} {self.model} - {self.price}"
    
    def mark_as_sold(self):
        """Mark car as sold."""
        self.status = 'sold'
        self.sold_at = timezone.now()
        self.save()
    
    def get_primary_image(self):
        """Get the primary image for the car."""
        return self.images.filter(is_primary=True).first() or self.images.first()


class CarImage(models.Model):
    """
    Images for car listings.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='cars/%Y/%m/%d/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.car}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary image per car."""
        if self.is_primary:
            CarImage.objects.filter(car=self.car, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class CarSpecification(models.Model):
    """
    Detailed specifications for cars.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='specification')
    
    # Performance
    horsepower = models.IntegerField(null=True, blank=True)
    torque = models.IntegerField(null=True, blank=True)
    acceleration_0_100 = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="0-100 km/h in seconds"
    )
    top_speed = models.IntegerField(null=True, blank=True, help_text="km/h")
    
    # Fuel efficiency
    fuel_consumption_city = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="km/l in city"
    )
    fuel_consumption_highway = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="km/l on highway"
    )
    
    # Dimensions
    length = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="mm")
    width = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="mm")
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="mm")
    weight = models.IntegerField(null=True, blank=True, help_text="kg")
    
    # Warranty and service
    warranty_remaining = models.CharField(max_length=100, null=True, blank=True)
    service_history = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Specs for {self.car}"
