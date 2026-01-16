from django.contrib import admin
from parts.models import CarPart, PartImage, PartCategory, PartCompatibility, CompanyStore, PartReview, PartReviewHelpfulness


@admin.register(PartCategory)
class PartCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CarPart)
class CarPartAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'price', 'seller', 'status', 'quantity_in_stock', 'created_at']
    list_filter = ['status', 'condition', 'category', 'created_at']
    search_fields = ['name', 'brand', 'part_number', 'seller__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'quantity_sold', 'rating', 'reviews_count']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'seller', 'category', 'name', 'description', 'part_number')
        }),
        ('Specifications', {
            'fields': ('condition', 'brand', 'model', 'weight', 'dimensions')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'quantity_in_stock', 'quantity_sold')
        }),
        ('Warranty', {
            'fields': ('warranty_months', 'warranty_description')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Ratings', {
            'fields': ('rating', 'reviews_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PartImage)
class PartImageAdmin(admin.ModelAdmin):
    list_display = ['part', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'uploaded_at']
    search_fields = ['part__name', 'part__brand']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(PartCompatibility)
class PartCompatibilityAdmin(admin.ModelAdmin):
    list_display = ['part', 'car_make', 'car_model', 'car_year_from', 'car_year_to']
    list_filter = ['car_make', 'car_model']
    search_fields = ['part__name', 'car_make', 'car_model']
    readonly_fields = ['id', 'created_at']


@admin.register(CompanyStore)
class CompanyStoreAdmin(admin.ModelAdmin):
    list_display = ['store_name', 'company', 'store_rating', 'is_verified', 'is_active']
    list_filter = ['is_verified', 'is_active', 'created_at']
    search_fields = ['store_name', 'company__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(PartReview)
class PartReviewAdmin(admin.ModelAdmin):
    list_display = ['part', 'reviewer', 'rating', 'is_verified_purchase', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'is_flagged', 'created_at']
    search_fields = ['part__name', 'reviewer__email', 'title', 'text']
    readonly_fields = ['id', 'helpful_count', 'unhelpful_count', 'created_at', 'updated_at']
    fieldsets = (
        ('Review Information', {
            'fields': ('id', 'reviewer', 'part', 'title', 'text')
        }),
        ('Ratings', {
            'fields': ('rating', 'quality_rating', 'value_rating', 'fitment_rating')
        }),
        ('Verification', {
            'fields': ('is_verified_purchase',)
        }),
        ('Engagement', {
            'fields': ('helpful_count', 'unhelpful_count')
        }),
        ('Moderation', {
            'fields': ('is_approved', 'is_flagged', 'flag_reason')
        }),
        ('Seller Response', {
            'fields': ('seller_response', 'seller_response_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(PartReviewHelpfulness)
class PartReviewHelpfulnessAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'vote_type', 'created_at']
    list_filter = ['vote_type', 'created_at']
    search_fields = ['review__part__name', 'user__email']
    readonly_fields = ['id', 'created_at']
