from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from users.models import CustomUser


class ForumCategory(models.Model):
    """
    Categories for forum discussions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField()
    icon = models.ImageField(upload_to='forum_categories/', null=True, blank=True)
    
    # Moderation
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Forum Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ExpertVerification(models.Model):
    """
    Track verified experts in the forum.
    """
    
    VERIFICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='expert_verification')
    
    # Expertise
    expertise_areas = models.JSONField(
        default=list,
        help_text="List of expertise areas: ['Engine Repair', 'Electrical', etc.]"
    )
    years_of_experience = models.IntegerField(validators=[MinValueValidator(0)])
    bio = models.TextField()
    
    # Verification
    status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    verification_document = models.FileField(upload_to='expert_verification/%Y/%m/')
    
    # Stats
    helpful_responses = models.IntegerField(default=0)
    total_responses = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-verified_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Expert"
    
    def get_helpfulness_rate(self):
        """Calculate helpfulness rate."""
        if self.total_responses == 0:
            return 0
        return (self.helpful_responses / self.total_responses) * 100


class ForumThread(models.Model):
    """
    Forum discussion thread.
    """
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='forum_threads')
    category = models.ForeignKey(ForumCategory, on_delete=models.SET_NULL, null=True, related_name='threads')
    
    # Content
    title = models.CharField(max_length=255, db_index=True)
    description = models.TextField()
    
    # Car context (optional)
    car_make = models.CharField(max_length=100, null=True, blank=True, db_index=True)
    car_model = models.CharField(max_length=100, null=True, blank=True)
    car_year = models.IntegerField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )
    is_pinned = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    # Engagement
    views_count = models.IntegerField(default=0)
    responses_count = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['author', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['car_make', 'car_model']),
        ]
    
    def __str__(self):
        return self.title
    
    def mark_as_resolved(self):
        """Mark thread as resolved."""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()


class ForumResponse(models.Model):
    """
    Response to a forum thread.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE, related_name='responses')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='forum_responses')
    
    # Content
    content = models.TextField()
    
    # Expert response
    is_expert_response = models.BooleanField(default=False)
    
    # AI response (for future implementation)
    is_ai_response = models.BooleanField(default=False)
    ai_confidence = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    
    # Engagement
    helpful_count = models.IntegerField(default=0)
    unhelpful_count = models.IntegerField(default=0)
    
    # Moderation
    is_approved = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    flag_reason = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_expert_response', '-helpful_count', 'created_at']
        indexes = [
            models.Index(fields=['thread', 'is_expert_response']),
            models.Index(fields=['author']),
        ]
    
    def __str__(self):
        return f"Response by {self.author.get_full_name()} on {self.thread.title}"
    
    def get_helpfulness_score(self):
        """Calculate helpfulness score."""
        total = self.helpful_count + self.unhelpful_count
        if total == 0:
            return 0
        return (self.helpful_count / total) * 100


class ResponseVote(models.Model):
    """
    Track votes on forum responses (helpful/unhelpful).
    """
    
    VOTE_CHOICES = (
        ('helpful', 'Helpful'),
        ('unhelpful', 'Unhelpful'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(ForumResponse, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='response_votes')
    
    vote_type = models.CharField(max_length=20, choices=VOTE_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('response', 'user')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.vote_type} on response"
