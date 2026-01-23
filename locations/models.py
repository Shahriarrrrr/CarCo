from django.db import models
from django.utils import timezone
import uuid
from users.models import CustomUser


class ShopLocation(models.Model):
    """
    Physical shop locations that appear on the map.
    Sellers can request to add their shop locations.
    Admin approval required before appearing on public map.
    """
    
    LOCATION_TYPE_CHOICES = [
        ('shop', 'Shop'),
        ('service', 'Service Center'),
        ('warehouse', 'Warehouse'),
    ]
    
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shop_locations',
        limit_choices_to={'is_seller': True}
    )
    store = models.ForeignKey(
        'parts.CompanyStore',
        on_delete=models.CASCADE,
        related_name='locations',
        null=True,
        blank=True,
        help_text='Associated company store (optional)'
    )
    
    # Basic Information
    name = models.CharField(max_length=255, help_text='Shop/Location name')
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='shop'
    )
    description = models.TextField(blank=True, null=True)
    
    # Location Coordinates
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        help_text='Longitude coordinate'
    )
    
    # Address
    address = models.CharField(max_length=500)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Bangladesh')
    
    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    
    # Operating Hours
    operating_hours = models.CharField(
        max_length=100,
        help_text='e.g., "9 AM - 9 PM" or "24/7"'
    )
    
    # Images
    image = models.ImageField(
        upload_to='shop_locations/%Y/%m/',
        null=True,
        blank=True,
        help_text='Shop photo'
    )
    
    # Status
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Admin Notes
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Admin notes for approval/rejection'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_locations'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'approval_status']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['city', 'approval_status']),
        ]
        verbose_name = 'Shop Location'
        verbose_name_plural = 'Shop Locations'
    
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"
    
    def approve(self, admin_user):
        """Approve the location."""
        self.approval_status = 'approved'
        self.approved_at = timezone.now()
        self.approved_by = admin_user
        self.save()
    
    def reject(self, admin_user, reason=None):
        """Reject the location."""
        self.approval_status = 'rejected'
        self.approved_by = admin_user
        if reason:
            self.admin_notes = reason
        self.save()
