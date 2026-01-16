from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CommentLike, CommentReply


@receiver(post_save, sender=CommentLike)
def update_like_count_on_save(sender, instance, created, **kwargs):
    """Update like count when a like is created."""
    if instance.like_type == 'comment' and instance.comment:
        instance.comment.likes_count = instance.comment.commentlike_set.filter(like_type='comment').count()
        instance.comment.save(update_fields=['likes_count'])
    elif instance.like_type == 'reply' and instance.reply:
        instance.reply.likes_count = instance.reply.commentlike_set.filter(like_type='reply').count()
        instance.reply.save(update_fields=['likes_count'])


@receiver(post_delete, sender=CommentLike)
def update_like_count_on_delete(sender, instance, **kwargs):
    """Update like count when a like is deleted."""
    if instance.like_type == 'comment' and instance.comment:
        instance.comment.likes_count = instance.comment.commentlike_set.filter(like_type='comment').count()
        instance.comment.save(update_fields=['likes_count'])
    elif instance.like_type == 'reply' and instance.reply:
        instance.reply.likes_count = instance.reply.commentlike_set.filter(like_type='reply').count()
        instance.reply.save(update_fields=['likes_count'])


@receiver(post_save, sender=CommentReply)
def update_comment_reply_count_on_save(sender, instance, created, **kwargs):
    """Update comment reply count when a reply is created."""
    if created:
        comment = instance.comment
        comment.replies_count = comment.replies.count()
        comment.save(update_fields=['replies_count'])


@receiver(post_delete, sender=CommentReply)
def update_comment_reply_count_on_delete(sender, instance, **kwargs):
    """Update comment reply count when a reply is deleted."""
    comment = instance.comment
    comment.replies_count = comment.replies.count()
    comment.save(update_fields=['replies_count'])
