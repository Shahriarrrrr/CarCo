from rest_framework import serializers
from payments.models import (
    Order, Payment, Invoice, Refund, Wallet, WalletTransaction, Discount
)


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders."""
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'buyer', 'buyer_name', 'seller', 'seller_name',
            'order_type', 'order_number', 'car_id', 'part_id',
            'item_name', 'item_description', 'quantity', 'unit_price',
            'subtotal', 'tax_amount', 'shipping_cost', 'discount_amount',
            'total_amount', 'shipping_address', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'billing_address', 'billing_city', 'billing_state',
            'billing_postal_code', 'billing_country', 'status',
            'tracking_number', 'tracking_url', 'buyer_notes', 'seller_notes',
            'created_at', 'confirmed_at', 'shipped_at', 'delivered_at',
            'cancelled_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'confirmed_at',
            'shipped_at', 'delivered_at', 'cancelled_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders."""
    
    class Meta:
        model = Order
        fields = [
            'order_type', 'car_id', 'part_id', 'item_name',
            'item_description', 'quantity', 'unit_price', 'subtotal',
            'tax_amount', 'shipping_cost', 'discount_amount',
            'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country',
            'billing_address', 'billing_city', 'billing_state',
            'billing_postal_code', 'billing_country', 'buyer_notes'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['buyer'] = request.user
        
        # Generate order number
        import uuid
        validated_data['order_number'] = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Calculate total
        order = Order(**validated_data)
        order.calculate_total()
        order.save()
        return order


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for payments."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'order', 'order_number', 'payment_method', 'amount',
            'currency', 'status', 'transaction_id', 'reference_number',
            'gateway_response', 'error_message', 'created_at',
            'processed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'gateway_response', 'error_message',
            'created_at', 'processed_at', 'updated_at'
        ]


class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments."""
    
    class Meta:
        model = Payment
        fields = ['order', 'payment_method', 'amount', 'currency']
    
    def create(self, validated_data):
        import uuid
        validated_data['transaction_id'] = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        return super().create(validated_data)


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for invoices."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_number', 'invoice_number', 'invoice_date',
            'due_date', 'status', 'line_items', 'notes', 'terms',
            'subtotal', 'tax_amount', 'total_amount', 'amount_paid',
            'amount_due', 'created_at', 'sent_at', 'viewed_at',
            'paid_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'invoice_number', 'invoice_date', 'created_at',
            'sent_at', 'viewed_at', 'paid_at', 'updated_at'
        ]


class RefundSerializer(serializers.ModelSerializer):
    """Serializer for refunds."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    class Meta:
        model = Refund
        fields = [
            'id', 'order', 'order_number', 'payment', 'refund_reason',
            'refund_amount', 'refund_percentage', 'status',
            'reason_description', 'admin_notes', 'requested_at',
            'approved_at', 'completed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'requested_at', 'approved_at', 'completed_at', 'updated_at'
        ]


class RefundCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating refunds."""
    
    class Meta:
        model = Refund
        fields = [
            'order', 'payment', 'refund_reason', 'refund_amount',
            'refund_percentage', 'reason_description'
        ]


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions."""
    
    class Meta:
        model = WalletTransaction
        fields = [
            'id', 'transaction_type', 'amount', 'description',
            'order_id', 'payment_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallets."""
    transactions = WalletTransactionSerializer(many=True, read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'user', 'user_name', 'balance', 'total_earned',
            'total_spent', 'transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'balance', 'total_earned', 'total_spent',
            'created_at', 'updated_at'
        ]


class DiscountSerializer(serializers.ModelSerializer):
    """Serializer for discounts."""
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = Discount
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value',
            'max_discount_amount', 'min_order_amount', 'max_uses',
            'max_uses_per_user', 'status', 'valid_from', 'valid_until',
            'times_used', 'is_valid', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'times_used', 'created_at', 'updated_at'
        ]
    
    def get_is_valid(self, obj):
        return obj.is_valid()


class DiscountValidateSerializer(serializers.Serializer):
    """Serializer for validating discount codes."""
    code = serializers.CharField(max_length=50)
    order_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    def validate_code(self, value):
        try:
            discount = Discount.objects.get(code=value)
            if not discount.is_valid():
                raise serializers.ValidationError("This discount code is not valid.")
            return discount
        except Discount.DoesNotExist:
            raise serializers.ValidationError("Discount code not found.")
    
    def validate(self, data):
        discount = data['code']
        order_amount = data['order_amount']
        
        if order_amount < discount.min_order_amount:
            raise serializers.ValidationError(
                f"Minimum order amount of {discount.min_order_amount} required."
            )
        
        return data


class DiscountApplySerializer(serializers.Serializer):
    """Serializer for applying discounts to orders."""
    discount_code = serializers.CharField(max_length=50)
    
    def validate_discount_code(self, value):
        try:
            discount = Discount.objects.get(code=value)
            if not discount.is_valid():
                raise serializers.ValidationError("This discount code is not valid.")
            return discount
        except Discount.DoesNotExist:
            raise serializers.ValidationError("Discount code not found.")
