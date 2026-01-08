from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid
from users.models import CustomUser


class PartCategory(models.Model):
    """
    Categories for car parts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='part_categories/', null=True, blank=True)
    parent_category = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Part Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CompanyStore(models.Model):
    """
    Company store profile for parts sellers.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='store_profile',
        limit_choices_to={'user_type': 'company'}
    )
    
    store_name = models.CharField(max_length=255)
    store_description = models.TextField()
    store_logo = models.ImageField(upload_to='store_logos/', null=True, blank=True)
    store_banner = models.ImageField(upload_to='store_banners/', null=True, blank=True)
    
    # Contact
    store_email = models.EmailField()
    store_phone = models.CharField(max_length=20)
    store_website = models.URLField(null=True, blank=True)
    
    # Location
    store_address = models.CharField(max_length=255)
    store_city = models.CharField(max_length=100)
    store_state = models.CharField(max_length=100)
    store_country = models.CharField(max_length=100)
    
    # Ratings
    store_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.IntegerField(default=0)
    
    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.store_name


class CarPart(models.Model):
    """
    Car parts listing model.
    """
    
    CONDITION_CHOICES = (
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('out_of_stock', 'Out of Stock'),
        ('discontinued', 'Discontinued'),
        ('pending', 'Pending Review'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='parts_for_sale')
    category = models.ForeignKey(PartCategory, on_delete=models.SET_NULL, null=True, related_name='parts')
    
    # Basic information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    part_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    
    # Specifications
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    brand = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    
    # Pricing and inventory
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity_in_stock = models.IntegerField(validators=[MinValueValidator(0)])
    quantity_sold = models.IntegerField(default=0)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    is_featured = models.BooleanField(default=False)
    
    # Warranty
    warranty_months = models.IntegerField(null=True, blank=True)
    warranty_description = models.TextField(null=True, blank=True)
    
    # Shipping
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg"
    )
    dimensions = models.CharField(max_length=100, null=True, blank=True, help_text="L x W x H in cm")
    
    # Ratings
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    reviews_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['brand']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.price}"
    
    def is_in_stock(self):
        """Check if part is in stock."""
        return self.quantity_in_stock > 0 and self.status == 'active'


class PartImage(models.Model):
    """
    Images for car parts.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.ForeignKey(CarPart, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='parts/%Y/%m/%d/')
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"Image for {self.part}"
    
    def save(self, *args, **kwargs):
        """Ensure only one primary image per part."""
        if self.is_primary:
            PartImage.objects.filter(part=self.part, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class PartCompatibility(models.Model):
    """
    Track which cars a part is compatible with.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.ForeignKey(CarPart, on_delete=models.CASCADE, related_name='compatibilities')
    
    # Car compatibility
    car_make = models.CharField(max_length=100, db_index=True)
    car_model = models.CharField(max_length=100, db_index=True)
    car_year_from = models.IntegerField()
    car_year_to = models.IntegerField()
    
    # Additional notes
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('part', 'car_make', 'car_model', 'car_year_from', 'car_year_to')
        ordering = ['car_make', 'car_model']
    
    def __str__(self):
        return f"{self.part.name} - {self.car_year_from}-{self.car_year_to} {self.car_make} {self.car_model}"
