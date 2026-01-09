from django.contrib import admin
from comments.models import Comment, CommentReply, CommentLike


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'content_type', 'object_id', 'likes_count', 'replies_count', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'is_flagged', 'created_at']
    search_fields = ['text', 'author__email']
    readonly_fields = ['id', 'likes_count', 'replies_count', 'created_at', 'updated_at']


@admin.register(CommentReply)
class CommentReplyAdmin(admin.ModelAdmin):
    list_display = ['author', 'comment', 'likes_count', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'is_flagged', 'created_at']
    search_fields = ['text', 'author__email']
    readonly_fields = ['id', 'likes_count', 'created_at', 'updated_at']


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'like_type', 'created_at']
    list_filter = ['like_type', 'created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at']
