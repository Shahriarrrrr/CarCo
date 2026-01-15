from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator, URLValidator
from django.utils import timezone
import uuid


class CustomUserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model for the CarCo app.
    Supports both individual buyers/sellers and company accounts.
    """
    
    USER_TYPE_CHOICES = (
        ('individual', 'Individual'),
        ('company', 'Company'),
    )
    
    VERIFICATION_STATUS_CHOICES = (
        ('unverified', 'Unverified'),
        ('pending', 'Pending Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )
    
    # Primary fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    username = None  # Remove the username field
    email = models.EmailField(unique=True, db_index=True)
    
    # Personal information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message='Phone number must be entered in the format: +999999999. Up to 15 digits allowed.'
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        null=True,
        blank=True,
        db_index=True
    )
    
    # Address information
    street_address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state_province = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    
    # Profile information
    profile_picture = models.ImageField(upload_to='profile_pics/%Y/%m/', null=True, blank=True)
    bio = models.TextField(max_length=500, null=True, blank=True)
    
    # Account type
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='individual'
    )
    
    # Company information (if user_type is 'company')
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_registration_number = models.CharField(max_length=100, null=True, blank=True, unique=True)
    company_website = models.URLField(null=True, blank=True)
    e_tin = models.CharField(max_length=50, null=True, blank=True, help_text='Electronic Tax Identification Number')
    trade_license_number = models.CharField(max_length=100, null=True, blank=True, help_text='Trade License Number')
    
    # Verification
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='unverified'
    )
    verification_document = models.FileField(upload_to='verification_docs/%Y/%m/', null=True, blank=True)
    
    # Account status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)
    is_buyer = models.BooleanField(default=True)
    
    # Ratings and reviews
    seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    seller_reviews_count = models.IntegerField(default=0)
    
    # Timestamps
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Account suspension
    is_suspended = models.BooleanField(default=False)
    suspension_reason = models.TextField(null=True, blank=True)
    suspension_until = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    class Meta:
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_seller']),
            models.Index(fields=['verification_status']),
        ]

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name
    
    def is_account_suspended(self):
        """Check if account is currently suspended."""
        if not self.is_suspended:
            return False
        if self.suspension_until and self.suspension_until <= timezone.now():
            self.is_suspended = False
            self.suspension_reason = None
            self.suspension_until = None
            self.save()
            return False
        return True
    
    def can_sell(self):
        """Check if user can sell items."""
        return self.is_seller and self.is_active and not self.is_account_suspended()
    
    def can_buy(self):
        """Check if user can buy items."""
        return self.is_buyer and self.is_active and not self.is_account_suspended()
    
    def update_last_login(self):
        """Update the last login timestamp."""
        self.last_login = timezone.now()
        self.save(update_fields=['last_login'])
