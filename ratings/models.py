from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from users.models import CustomUser


class Review(models.Model):
    """
    User reviews for sellers.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_given')
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='reviews_received')
    
    # Review content
    title = models.CharField(max_length=255)
    text = models.TextField()
    
    # Rating
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_index=True
    )
    
    # Aspects (optional detailed ratings)
    communication_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    item_accuracy_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    shipping_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Verification
    is_verified_purchase = models.BooleanField(default=False)
    
    # Engagement
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, null=True, blank=True)
    
    # Seller response
    seller_response = models.TextField(null=True, blank=True)
    seller_response_date = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('reviewer', 'seller')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'rating']),
            models.Index(fields=['reviewer']),
        ]
    
    def __str__(self):
        return f"Review by {self.reviewer.get_full_name()} for {self.seller.get_full_name()}"


class Rating(models.Model):
    """
    Numerical ratings for sellers (aggregated from reviews).
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='seller_rating_summary')
    
    # Overall rating
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    total_reviews = models.IntegerField(default=0)
    
    # Rating distribution
    five_star_count = models.IntegerField(default=0)
    four_star_count = models.IntegerField(default=0)
    three_star_count = models.IntegerField(default=0)
    two_star_count = models.IntegerField(default=0)
    one_star_count = models.IntegerField(default=0)
    
    # Aspect ratings
    average_communication = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    average_item_accuracy = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    average_shipping = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-average_rating']
    
    def __str__(self):
        return f"Rating for {self.seller.get_full_name()}"
    
    def update_from_reviews(self):
        """Recalculate ratings from all reviews."""
        reviews = Review.objects.filter(seller=self.seller, is_approved=True)
        
        if not reviews.exists():
            self.average_rating = 0.0
            self.total_reviews = 0
            self.save()
            return
        
        # Calculate overall rating
        self.total_reviews = reviews.count()
        self.average_rating = sum(r.rating for r in reviews) / self.total_reviews
        
        # Calculate distribution
        self.five_star_count = reviews.filter(rating=5).count()
        self.four_star_count = reviews.filter(rating=4).count()
        self.three_star_count = reviews.filter(rating=3).count()
        self.two_star_count = reviews.filter(rating=2).count()
        self.one_star_count = reviews.filter(rating=1).count()
        
        # Calculate aspect ratings
        comm_ratings = [r.communication_rating for r in reviews if r.communication_rating]
        if comm_ratings:
            self.average_communication = sum(comm_ratings) / len(comm_ratings)
        
        acc_ratings = [r.item_accuracy_rating for r in reviews if r.item_accuracy_rating]
        if acc_ratings:
            self.average_item_accuracy = sum(acc_ratings) / len(acc_ratings)
        
        ship_ratings = [r.shipping_rating for r in reviews if r.shipping_rating]
        if ship_ratings:
            self.average_shipping = sum(ship_ratings) / len(ship_ratings)
        
        self.save()


class ReviewHelpfulness(models.Model):
    """
    Track helpful/unhelpful votes on reviews.
    """
    
    VOTE_CHOICES = (
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='helpfulness_votes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='review_helpfulness_votes')
    
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('review', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vote_type} on review"
