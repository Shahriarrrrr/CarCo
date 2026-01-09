from django.contrib import admin
from forum.models import ForumCategory, ForumThread, ForumResponse, ExpertVerification, ResponseVote


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ForumThread)
class ForumThreadAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'responses_count', 'views_count', 'created_at']
    list_filter = ['status', 'is_pinned', 'is_featured', 'category', 'created_at']
    search_fields = ['title', 'description', 'author__email', 'car_make', 'car_model']
    readonly_fields = ['id', 'views_count', 'responses_count', 'created_at', 'updated_at', 'resolved_at']


@admin.register(ForumResponse)
class ForumResponseAdmin(admin.ModelAdmin):
    list_display = ['thread', 'author', 'is_expert_response', 'is_approved', 'helpful_count', 'created_at']
    list_filter = ['is_expert_response', 'is_approved', 'is_flagged', 'created_at']
    search_fields = ['content', 'author__email', 'thread__title']
    readonly_fields = ['id', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at']


@admin.register(ExpertVerification)
class ExpertVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'years_of_experience', 'helpful_responses', 'verified_at']
    list_filter = ['status', 'verified_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'expertise_areas']
    readonly_fields = ['id', 'created_at', 'updated_at', 'verified_at']


@admin.register(ResponseVote)
class ResponseVoteAdmin(admin.ModelAdmin):
    list_display = ['response', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__email', 'response__thread__title']
    readonly_fields = ['id', 'created_at']
