from django.contrib import admin
from django.utils.html import format_html
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin interface for CustomUser model."""
    
    list_display = [
        'email', 'get_full_name', 'user_type', 'is_seller', 'verification_status',
        'is_active', 'is_suspended', 'seller_rating', 'date_joined'
    ]
    list_filter = [
        'user_type', 'is_seller', 'is_buyer', 'verification_status',
        'is_active', 'is_suspended', 'email_verified', 'phone_verified',
        'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number', 'company_name']
    readonly_fields = [
        'id', 'date_joined', 'updated_at', 'last_login',
        'seller_rating', 'seller_reviews_count'
    ]
    
    fieldsets = (
        ('Account Information', {
            'fields': ('id', 'email', 'password', 'user_type')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'profile_picture', 'bio')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'street_address', 'city', 'state_province', 'postal_code', 'country')
        }),
        ('Company Information', {
            'fields': ('company_name', 'company_registration_number', 'company_website'),
            'classes': ('collapse',)
        }),
        ('Verification', {
            'fields': ('email_verified', 'phone_verified', 'verification_status', 'verification_document')
        }),
        ('Account Status', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_seller', 'is_buyer')
        }),
        ('Seller Information', {
            'fields': ('seller_rating', 'seller_reviews_count'),
            'classes': ('collapse',)
        }),
        ('Suspension', {
            'fields': ('is_suspended', 'suspension_reason', 'suspension_until'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_verified', 'make_unverified', 'enable_seller', 'disable_seller', 'suspend_account', 'unsuspend_account']
    
    def get_full_name(self, obj):
        """Display user's full name."""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    
    def make_verified(self, request, queryset):
        """Mark selected users as verified."""
        updated = queryset.update(verification_status='verified')
        self.message_user(request, f'{updated} user(s) marked as verified.')
    make_verified.short_description = 'Mark selected users as verified'
    
    def make_unverified(self, request, queryset):
        """Mark selected users as unverified."""
        updated = queryset.update(verification_status='unverified')
        self.message_user(request, f'{updated} user(s) marked as unverified.')
    make_unverified.short_description = 'Mark selected users as unverified'
    
    def enable_seller(self, request, queryset):
        """Enable seller mode for selected users."""
        updated = queryset.update(is_seller=True)
        self.message_user(request, f'Seller mode enabled for {updated} user(s).')
    enable_seller.short_description = 'Enable seller mode'
    
    def disable_seller(self, request, queryset):
        """Disable seller mode for selected users."""
        updated = queryset.update(is_seller=False)
        self.message_user(request, f'Seller mode disabled for {updated} user(s).')
    disable_seller.short_description = 'Disable seller mode'
    
    def suspend_account(self, request, queryset):
        """Suspend selected user accounts."""
        updated = queryset.update(is_suspended=True)
        self.message_user(request, f'{updated} account(s) suspended.')
    suspend_account.short_description = 'Suspend selected accounts'
    
    def unsuspend_account(self, request, queryset):
        """Unsuspend selected user accounts."""
        updated = queryset.update(is_suspended=False, suspension_reason=None, suspension_until=None)
        self.message_user(request, f'{updated} account(s) unsuspended.')
    unsuspend_account.short_description = 'Unsuspend selected accounts'