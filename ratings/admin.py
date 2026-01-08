from django.contrib import admin
from ratings.models import Review, Rating, ReviewHelpfulness


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'seller', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'is_flagged', 'created_at']
    search_fields = ['title', 'text', 'reviewer__email', 'seller__email']
    readonly_fields = ['id', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['seller', 'average_rating', 'total_reviews']
    search_fields = ['seller__email', 'seller__first_name', 'seller__last_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['user__email', 'review__title']
    readonly_fields = ['id', 'created_at']
