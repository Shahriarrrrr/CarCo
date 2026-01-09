"""
SSL Commerz Callback URL Handlers
Handles payment success, failure, and cancellation callbacks
"""

from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from payments.sslcommerz import SSLCommerczPaymentGateway


@csrf_exempt
def sslcommerz_success(request):
    """Handle SSL Commerz payment success callback"""
    if request.method == 'POST':
        gateway = SSLCommerczPaymentGateway(is_sandbox=True)
        result = gateway.handle_payment_success(request.POST)
        
        if result['success']:
            return JsonResponse({
                'status': 'success',
                'message': result['message'],
                'order_id': result.get('order_id'),
                'transaction_id': result.get('transaction_id')
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result['message'],
                'error': result.get('error')
            }, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def sslcommerz_fail(request):
    """Handle SSL Commerz payment failure callback"""
    if request.method == 'POST':
        gateway = SSLCommerczPaymentGateway(is_sandbox=True)
        result = gateway.handle_payment_fail(request.POST)
        
        return JsonResponse({
            'status': 'failed',
            'message': result['message'],
            'error': result.get('error')
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def sslcommerz_cancel(request):
    """Handle SSL Commerz payment cancellation callback"""
    if request.method == 'POST':
        gateway = SSLCommerczPaymentGateway(is_sandbox=True)
        result = gateway.handle_payment_cancel(request.POST)
        
        return JsonResponse({
            'status': 'cancelled',
            'message': result['message']
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


# URL patterns
urlpatterns = [
    path('sslcommerz/success/', sslcommerz_success, name='sslcommerz_success'),
    path('sslcommerz/fail/', sslcommerz_fail, name='sslcommerz_fail'),
    path('sslcommerz/cancel/', sslcommerz_cancel, name='sslcommerz_cancel'),
]
