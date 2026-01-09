from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from payments.models import (
    Order, Payment, Invoice, Refund, Wallet, WalletTransaction, Discount
)
from payments.serializers import (
    OrderSerializer, OrderCreateSerializer, PaymentSerializer,
    PaymentCreateSerializer, InvoiceSerializer, RefundSerializer,
    RefundCreateSerializer, WalletSerializer, DiscountSerializer,
    DiscountValidateSerializer, DiscountApplySerializer
)
from payments.sslcommerz import SSLCommerczPaymentGateway


class OrderPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get orders for the current user (as buyer or seller)."""
        user = self.request.user
        return Order.objects.filter(
            models.Q(buyer=user) | models.Q(seller=user)
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new order."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get seller from car or part
        order_type = serializer.validated_data.get('order_type')
        seller = None
        
        if order_type == 'car':
            from cars.models import Car
            car_id = serializer.validated_data.get('car_id')
            try:
                car = Car.objects.get(id=car_id)
                seller = car.seller
            except Car.DoesNotExist:
                return Response(
                    {'detail': 'Car not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        elif order_type == 'part':
            from parts.models import CarPart
            part_id = serializer.validated_data.get('part_id')
            try:
                part = CarPart.objects.get(id=part_id)
                seller = part.seller
            except CarPart.DoesNotExist:
                return Response(
                    {'detail': 'Part not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if not seller:
            return Response(
                {'detail': 'Seller not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order = serializer.save(seller=seller)
        return Response(
            OrderSerializer(order, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm an order."""
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'detail': 'Only the buyer can confirm the order.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status != 'pending':
            return Response(
                {'detail': 'Order cannot be confirmed in its current status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.mark_as_confirmed()
        return Response(
            OrderSerializer(order, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark order as shipped."""
        order = self.get_object()
        
        if order.seller != request.user:
            return Response(
                {'detail': 'Only the seller can mark the order as shipped.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tracking_number = request.data.get('tracking_number')
        tracking_url = request.data.get('tracking_url')
        
        order.mark_as_shipped(tracking_number, tracking_url)
        return Response(
            OrderSerializer(order, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Mark order as delivered."""
        order = self.get_object()
        
        if order.buyer != request.user:
            return Response(
                {'detail': 'Only the buyer can confirm delivery.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order.mark_as_delivered()
        return Response(
            OrderSerializer(order, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order."""
        order = self.get_object()
        
        if order.buyer != request.user and order.seller != request.user:
            return Response(
                {'detail': 'Only buyer or seller can cancel the order.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if order.status not in ['pending', 'confirmed']:
            return Response(
                {'detail': 'Order cannot be cancelled in its current status.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.cancel_order()
        return Response(
            OrderSerializer(order, context={'request': request}).data
        )


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payments.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PaymentSerializer
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get payments for the current user's orders."""
        user = self.request.user
        return Payment.objects.filter(
            models.Q(order__buyer=user) | models.Q(order__seller=user)
        ).order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new payment."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.validated_data['order']
        
        # Check if user is the buyer
        if order.buyer != request.user:
            return Response(
                {'detail': 'Only the buyer can make payment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if payment already exists
        if Payment.objects.filter(order=order).exists():
            return Response(
                {'detail': 'Payment already exists for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment = serializer.save()
        
        # TODO: Integrate with payment gateway (Stripe, PayPal, etc.)
        # For now, mark as completed
        payment.mark_as_completed()
        
        return Response(
            PaymentSerializer(payment, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry a failed payment."""
        payment = self.get_object()
        
        if payment.order.buyer != request.user:
            return Response(
                {'detail': 'Only the buyer can retry payment.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if payment.status != 'failed':
            return Response(
                {'detail': 'Only failed payments can be retried.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # TODO: Retry payment with gateway
        payment.status = 'processing'
        payment.save()
        
        return Response(
            PaymentSerializer(payment, context={'request': request}).data
        )
    
    @action(detail=False, methods=['post'])
    def initiate_sslcommerz(self, request):
        """Initiate SSL Commerz payment."""
        order_id = request.data.get('order_id')
        
        try:
            order = Order.objects.get(id=order_id, buyer=request.user)
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create payment record
        payment, created = Payment.objects.get_or_create(
            order=order,
            defaults={
                'payment_method': 'sslcommerz',
                'amount': order.total_amount,
                'currency': 'BDT',
                'status': 'pending'
            }
        )
        
        # Initialize SSL Commerz gateway
        gateway = SSLCommerczPaymentGateway(is_sandbox=True)
        result = gateway.initiate_payment(order)
        
        if result['success']:
            return Response({
                'success': True,
                'gateway_url': result['gateway_url'],
                'session_id': result['session_id'],
                'message': 'Payment session initiated'
            })
        else:
            return Response({
                'success': False,
                'error': result['error'],
                'message': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


class InvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing invoices.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InvoiceSerializer
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get invoices for the current user's orders."""
        user = self.request.user
        return Invoice.objects.filter(
            models.Q(order__buyer=user) | models.Q(order__seller=user)
        ).order_by('-invoice_date')
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send invoice to buyer."""
        invoice = self.get_object()
        
        if invoice.order.seller != request.user:
            return Response(
                {'detail': 'Only the seller can send the invoice.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        invoice.mark_as_sent()
        # TODO: Send email to buyer
        
        return Response(
            InvoiceSerializer(invoice, context={'request': request}).data
        )


class RefundViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing refunds.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = RefundSerializer
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get refunds for the current user's orders."""
        user = self.request.user
        return Refund.objects.filter(
            models.Q(order__buyer=user) | models.Q(order__seller=user)
        ).order_by('-requested_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RefundCreateSerializer
        return RefundSerializer
    
    def create(self, request, *args, **kwargs):
        """Request a refund."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        order = serializer.validated_data['order']
        
        # Check if user is the buyer
        if order.buyer != request.user:
            return Response(
                {'detail': 'Only the buyer can request a refund.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if order has payment
        try:
            payment = Payment.objects.get(order=order)
        except Payment.DoesNotExist:
            return Response(
                {'detail': 'No payment found for this order.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund = serializer.save(payment=payment)
        
        return Response(
            RefundSerializer(refund, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a refund (admin only)."""
        refund = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only admins can approve refunds.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund.approve_refund()
        return Response(
            RefundSerializer(refund, context={'request': request}).data
        )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a refund."""
        refund = self.get_object()
        
        if not request.user.is_staff:
            return Response(
                {'detail': 'Only admins can complete refunds.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        refund.complete_refund()
        return Response(
            RefundSerializer(refund, context={'request': request}).data
        )


class WalletViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing wallet information.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WalletSerializer
    
    def get_queryset(self):
        """Get wallet for the current user."""
        return Wallet.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get current user's wallet."""
        try:
            wallet = Wallet.objects.get(user=request.user)
            serializer = self.get_serializer(wallet)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            return Response(
                {'detail': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class DiscountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing and validating discounts.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DiscountSerializer
    pagination_class = OrderPagination
    
    def get_queryset(self):
        """Get active discounts."""
        return Discount.objects.filter(status='active')
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Validate a discount code."""
        serializer = DiscountValidateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        discount = serializer.validated_data['code']
        discount_amount = discount.calculate_discount(
            serializer.validated_data['order_amount']
        )
        
        return Response({
            'valid': True,
            'discount_code': discount.code,
            'discount_amount': discount_amount,
            'discount_type': discount.discount_type,
            'discount_value': discount.discount_value
        })
    
    @action(detail=False, methods=['post'])
    def apply(self, request):
        """Apply a discount to an order."""
        serializer = DiscountApplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        discount = serializer.validated_data['discount_code']
        
        return Response({
            'applied': True,
            'discount_code': discount.code,
            'discount_type': discount.discount_type,
            'discount_value': discount.discount_value
        })


from django.db import models
