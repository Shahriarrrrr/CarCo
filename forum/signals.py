from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ResponseVote, ForumResponse


@receiver(post_save, sender=ResponseVote)
def update_response_counts_on_vote_save(sender, instance, created, **kwargs):
    """Update response helpful/unhelpful counts when vote is saved."""
    response = instance.response
    response.helpful_count = response.votes.filter(vote_type='helpful').count()
    response.unhelpful_count = response.votes.filter(vote_type='unhelpful').count()
    response.save(update_fields=['helpful_count', 'unhelpful_count'])


@receiver(post_delete, sender=ResponseVote)
def update_response_counts_on_vote_delete(sender, instance, **kwargs):
    """Update response helpful/unhelpful counts when vote is deleted."""
    response = instance.response
    response.helpful_count = response.votes.filter(vote_type='helpful').count()
    response.unhelpful_count = response.votes.filter(vote_type='unhelpful').count()
    response.save(update_fields=['helpful_count', 'unhelpful_count'])


@receiver(post_save, sender=ForumResponse)
def update_thread_response_count_on_save(sender, instance, created, **kwargs):
    """Update thread response count when a response is created."""
    if created:
        thread = instance.thread
        thread.responses_count = thread.responses.count()
        thread.save(update_fields=['responses_count'])


@receiver(post_delete, sender=ForumResponse)
def update_thread_response_count_on_delete(sender, instance, **kwargs):
    """Update thread response count when a response is deleted."""
    thread = instance.thread
    thread.responses_count = thread.responses.count()
    thread.save(update_fields=['responses_count'])
