from django.contrib import admin
from django.utils.html import format_html
from .models import ShopLocation


@admin.register(ShopLocation)
class ShopLocationAdmin(admin.ModelAdmin):
    """Admin interface for managing shop locations."""
    
    list_display = [
        'name', 'seller_link', 'location_type', 'city', 
        'approval_status_badge', 'is_active', 'created_at'
    ]
    list_filter = [
        'approval_status', 'location_type', 'is_active', 
        'city', 'country', 'created_at'
    ]
    search_fields = ['name', 'seller__email', 'seller__first_name', 'seller__last_name', 
                     'address', 'city', 'description', 'phone']
    readonly_fields = ['id', 'created_at', 'updated_at', 'approved_at', 'approved_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'seller', 'store', 'name', 'location_type', 'description')
        }),
        ('Location Coordinates', {
            'fields': ('latitude', 'longitude'),
            'description': 'Enter the exact coordinates for map placement'
        }),
        ('Address Details', {
            'fields': ('address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'website', 'operating_hours')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Approval Status', {
            'fields': ('approval_status', 'is_active', 'admin_notes'),
            'classes': ('wide',)
        }),
        ('Approval Information', {
            'fields': ('approved_at', 'approved_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_locations', 'reject_locations', 'activate_locations', 'deactivate_locations']
    
    def seller_link(self, obj):
        """Display seller with link to their profile."""
        return format_html(
            '<a href="/admin/users/customuser/{}/change/">{}</a>',
            obj.seller.id,
            obj.seller.get_full_name() or obj.seller.email
        )
    seller_link.short_description = 'Seller'
    
    def approval_status_badge(self, obj):
        """Display approval status with colored badge."""
        colors = {
            'pending': '#fbbf24',  # yellow
            'approved': '#10b981',  # green
            'rejected': '#ef4444',  # red
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.approval_status, '#6b7280'),
            obj.get_approval_status_display()
        )
    approval_status_badge.short_description = 'Status'
    
    def approve_locations(self, request, queryset):
        """Approve selected locations."""
        count = 0
        for location in queryset.exclude(approval_status='approved'):
            location.approve(request.user)
            count += 1
        self.message_user(request, f'{count} location(s) approved successfully.')
    approve_locations.short_description = 'Approve selected locations'
    
    def reject_locations(self, request, queryset):
        """Reject selected locations."""
        count = 0
        for location in queryset.exclude(approval_status='rejected'):
            location.reject(request.user, reason='Rejected via bulk action')
            count += 1
        self.message_user(request, f'{count} location(s) rejected.')
    reject_locations.short_description = 'Reject selected locations'
    
    def activate_locations(self, request, queryset):
        """Activate selected locations."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} location(s) activated.')
    activate_locations.short_description = 'Activate selected locations'
    
    def deactivate_locations(self, request, queryset):
        """Deactivate selected locations."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} location(s) deactivated.')
    deactivate_locations.short_description = 'Deactivate selected locations'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related('seller', 'store', 'approved_by')
