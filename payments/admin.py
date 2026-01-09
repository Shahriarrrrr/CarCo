from django.contrib import admin
from payments.models import (
    Order, Payment, Invoice, Refund, Wallet, WalletTransaction, Discount
)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'seller', 'order_type', 'total_amount', 'status', 'created_at']
    list_filter = ['order_type', 'status', 'created_at']
    search_fields = ['order_number', 'buyer__email', 'seller__email', 'item_name']
    readonly_fields = ['id', 'order_number', 'created_at', 'updated_at']
    fieldsets = (
        ('Order Information', {
            'fields': ('id', 'order_number', 'order_type', 'buyer', 'seller', 'status')
        }),
        ('Item Details', {
            'fields': ('car_id', 'part_id', 'item_name', 'item_description', 'quantity', 'unit_price')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 'discount_amount', 'total_amount')
        }),
        ('Shipping Address', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country')
        }),
        ('Billing Address', {
            'fields': ('billing_address', 'billing_city', 'billing_state', 'billing_postal_code', 'billing_country')
        }),
        ('Tracking', {
            'fields': ('tracking_number', 'tracking_url')
        }),
        ('Notes', {
            'fields': ('buyer_notes', 'seller_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'confirmed_at', 'shipped_at', 'delivered_at', 'cancelled_at', 'updated_at')
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'order', 'payment_method', 'amount', 'status', 'created_at']
    list_filter = ['payment_method', 'status', 'created_at']
    search_fields = ['transaction_id', 'order__order_number', 'reference_number']
    readonly_fields = ['id', 'transaction_id', 'created_at', 'updated_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'order', 'invoice_date', 'due_date', 'status', 'total_amount']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'order__order_number']
    readonly_fields = ['id', 'invoice_number', 'created_at', 'updated_at']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'refund_reason', 'refund_amount', 'status', 'requested_at']
    list_filter = ['refund_reason', 'status', 'requested_at']
    search_fields = ['order__order_number', 'reason_description']
    readonly_fields = ['id', 'requested_at', 'updated_at']


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'balance', 'total_earned', 'total_spent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['id', 'wallet', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['wallet__user__email', 'description']
    readonly_fields = ['id', 'created_at']


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'status', 'valid_from', 'valid_until', 'times_used']
    list_filter = ['discount_type', 'status', 'valid_from']
    search_fields = ['code', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
