from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from users.models import CustomUser


class Order(models.Model):
    """
    Represents a purchase order for cars or parts.
    """
    
    ORDER_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    ORDER_TYPE_CHOICES = (
        ('car', 'Car'),
        ('part', 'Car Part'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Buyer and seller
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='purchases')
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sales')
    
    # Order details
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, db_index=True)
    order_number = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Item references
    car_id = models.UUIDField(null=True, blank=True, db_index=True)
    part_id = models.UUIDField(null=True, blank=True, db_index=True)
    
    # Item details (snapshot at time of order)
    item_name = models.CharField(max_length=255)
    item_description = models.TextField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)], default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Shipping information
    shipping_address = models.CharField(max_length=255)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100)
    
    # Billing information
    billing_address = models.CharField(max_length=255)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=100)
    billing_postal_code = models.CharField(max_length=20)
    billing_country = models.CharField(max_length=100)
    
    # Order status
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Tracking
    tracking_number = models.CharField(max_length=100, null=True, blank=True)
    tracking_url = models.URLField(null=True, blank=True)
    
    # Notes
    buyer_notes = models.TextField(null=True, blank=True)
    seller_notes = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['order_type']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.item_name}"
    
    def calculate_total(self):
        """Calculate total amount."""
        self.total_amount = self.subtotal + self.tax_amount + self.shipping_cost - self.discount_amount
        return self.total_amount
    
    def mark_as_confirmed(self):
        """Mark order as confirmed."""
        self.status = 'confirmed'
        self.confirmed_at = timezone.now()
        self.save()
    
    def mark_as_shipped(self, tracking_number=None, tracking_url=None):
        """Mark order as shipped."""
        self.status = 'shipped'
        self.shipped_at = timezone.now()
        if tracking_number:
            self.tracking_number = tracking_number
        if tracking_url:
            self.tracking_url = tracking_url
        self.save()
    
    def mark_as_delivered(self):
        """Mark order as delivered."""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save()
    
    def cancel_order(self):
        """Cancel the order."""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.save()


class Payment(models.Model):
    """
    Payment records for orders.
    """
    
    PAYMENT_METHOD_CHOICES = (
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('bank_transfer', 'Bank Transfer'),
        ('wallet', 'Wallet Balance'),
        ('other', 'Other'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, default='USD')
    
    # Payment status
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Transaction details
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    reference_number = models.CharField(max_length=100, null=True, blank=True)
    
    # Gateway response
    gateway_response = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"
    
    def mark_as_completed(self):
        """Mark payment as completed."""
        self.status = 'completed'
        self.processed_at = timezone.now()
        self.save()
        # Update order status
        self.order.mark_as_confirmed()
    
    def mark_as_failed(self, error_message=None):
        """Mark payment as failed."""
        self.status = 'failed'
        if error_message:
            self.error_message = error_message
        self.save()


class Invoice(models.Model):
    """
    Invoice for orders.
    """
    
    INVOICE_STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='draft',
        db_index=True
    )
    
    # Invoice content (JSON for flexibility)
    line_items = models.JSONField(default=list)
    notes = models.TextField(null=True, blank=True)
    terms = models.TextField(null=True, blank=True)
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    amount_due = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def mark_as_sent(self):
        """Mark invoice as sent."""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save()
    
    def mark_as_viewed(self):
        """Mark invoice as viewed."""
        self.status = 'viewed'
        self.viewed_at = timezone.now()
        self.save()
    
    def mark_as_paid(self):
        """Mark invoice as paid."""
        self.status = 'paid'
        self.paid_at = timezone.now()
        self.amount_paid = self.total_amount
        self.amount_due = 0
        self.save()


class Refund(models.Model):
    """
    Refund records for orders.
    """
    
    REFUND_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    )
    
    REFUND_REASON_CHOICES = (
        ('item_defective', 'Item Defective'),
        ('item_not_as_described', 'Item Not As Described'),
        ('buyer_changed_mind', 'Buyer Changed Mind'),
        ('seller_cancelled', 'Seller Cancelled'),
        ('duplicate_order', 'Duplicate Order'),
        ('payment_error', 'Payment Error'),
        ('other', 'Other'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    
    # Refund details
    refund_reason = models.CharField(max_length=50, choices=REFUND_REASON_CHOICES)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    refund_percentage = models.IntegerField(default=100, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=REFUND_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Refund details
    reason_description = models.TextField()
    admin_notes = models.TextField(null=True, blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Refund for Order {self.order.order_number}"
    
    def approve_refund(self):
        """Approve the refund."""
        self.status = 'approved'
        self.approved_at = timezone.now()
        self.save()
    
    def complete_refund(self):
        """Mark refund as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
        # Update order status
        self.order.status = 'refunded'
        self.order.save()


class Wallet(models.Model):
    """
    User wallet for storing balance.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    
    # Balance
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Wallets"
    
    def __str__(self):
        return f"Wallet for {self.user.get_full_name()}"
    
    def add_balance(self, amount, description=""):
        """Add balance to wallet."""
        self.balance += amount
        self.total_earned += amount
        self.save()
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            description=description
        )
    
    def deduct_balance(self, amount, description=""):
        """Deduct balance from wallet."""
        if self.balance >= amount:
            self.balance -= amount
            self.total_spent += amount
            self.save()
            # Create transaction record
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='debit',
                amount=amount,
                description=description
            )
            return True
        return False


class WalletTransaction(models.Model):
    """
    Transaction history for wallet.
    """
    
    TRANSACTION_TYPE_CHOICES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.CharField(max_length=255)
    
    # Related objects
    order_id = models.UUIDField(null=True, blank=True)
    payment_id = models.UUIDField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} for {self.wallet.user.get_full_name()}"


class Discount(models.Model):
    """
    Discount codes and promotional offers.
    """
    
    DISCOUNT_TYPE_CHOICES = (
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('expired', 'Expired'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Discount details
    code = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField()
    
    # Discount type
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    max_discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    # Conditions
    min_order_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    max_uses = models.IntegerField(null=True, blank=True)
    max_uses_per_user = models.IntegerField(default=1)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', db_index=True)
    
    # Dates
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Usage tracking
    times_used = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Discount {self.code}"
    
    def is_valid(self):
        """Check if discount is valid."""
        now = timezone.now()
        if self.status != 'active':
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.times_used >= self.max_uses:
            return False
        return True
    
    def calculate_discount(self, amount):
        """Calculate discount amount."""
        if self.discount_type == 'percentage':
            discount = (amount * self.discount_value) / 100
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        else:
            discount = self.discount_value
        return discount
