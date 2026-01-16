from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ReviewHelpfulness, Review, Rating


@receiver(post_save, sender=ReviewHelpfulness)
def update_review_helpfulness_on_save(sender, instance, created, **kwargs):
    """Update review helpful/unhelpful counts when vote is saved."""
    review = instance.review
    review.helpful_count = review.helpfulness_votes.filter(vote_type='helpful').count()
    review.unhelpful_count = review.helpfulness_votes.filter(vote_type='unhelpful').count()
    review.save(update_fields=['helpful_count', 'unhelpful_count'])


@receiver(post_delete, sender=ReviewHelpfulness)
def update_review_helpfulness_on_delete(sender, instance, **kwargs):
    """Update review helpful/unhelpful counts when vote is deleted."""
    review = instance.review
    review.helpful_count = review.helpfulness_votes.filter(vote_type='helpful').count()
    review.unhelpful_count = review.helpfulness_votes.filter(vote_type='unhelpful').count()
    review.save(update_fields=['helpful_count', 'unhelpful_count'])


@receiver(post_save, sender=Review)
def update_seller_rating_on_review_save(sender, instance, created, **kwargs):
    """Update seller rating when a review is created or updated."""
    if instance.is_approved:
        rating, _ = Rating.objects.get_or_create(seller=instance.seller)
        rating.update_from_reviews()


@receiver(post_delete, sender=Review)
def update_seller_rating_on_review_delete(sender, instance, **kwargs):
    """Update seller rating when a review is deleted."""
    try:
        rating = Rating.objects.get(seller=instance.seller)
        rating.update_from_reviews()
    except Rating.DoesNotExist:
        pass
