"""
SSL Commerz Payment Gateway Integration
Custom implementation for SSL Commerz payment processing
"""

import requests
import json
from django.conf import settings
from payments.models import Payment, Order
from django.utils import timezone


class SSLCommerczPaymentGateway:
    """
    SSL Commerz Payment Gateway Handler
    Handles payment initiation, validation, and processing
    """
    
    # SSL Commerz API endpoints
    SANDBOX_URL = 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php'
    PRODUCTION_URL = 'https://securepay.sslcommerz.com/gwprocess/v4/api.php'
    
    VALIDATION_URL = 'https://securepay.sslcommerz.com/validator/api/validationApi.php'
    SANDBOX_VALIDATION_URL = 'https://sandbox.sslcommerz.com/validator/api/validationApi.php'
    
    def __init__(self, is_sandbox=True):
        """
        Initialize SSL Commerz Gateway
        
        Args:
            is_sandbox (bool): Use sandbox or production environment
        """
        self.is_sandbox = is_sandbox
        self.store_id = settings.SSLCOMMERZ_STORE_ID
        self.store_password = settings.SSLCOMMERZ_STORE_PASSWD
        self.api_url = self.SANDBOX_URL if is_sandbox else self.PRODUCTION_URL
        self.validation_url = self.SANDBOX_VALIDATION_URL if is_sandbox else self.VALIDATION_URL
    
    def initiate_payment(self, order):
        """
        Initiate payment session with SSL Commerz
        
        Args:
            order (Order): Order object to process
            
        Returns:
            dict: Response containing payment gateway URL or error
        """
        try:
            # Get customer name with fallback
            cus_name = order.buyer.get_full_name() if hasattr(order.buyer, 'get_full_name') else 'Customer'
            if not cus_name or cus_name.strip() == '':
                cus_name = order.buyer.username or order.buyer.email.split('@')[0] if order.buyer.email else 'Customer'
            
            # Prepare payment data
            payload = {
                'store_id': self.store_id,
                'store_passwd': self.store_password,
                'total_amount': str(order.total_amount),
                'currency': 'BDT',
                'tran_id': str(order.order_number),
                'success_url': settings.SSLCOMMERZ_SUCCESS_URL,
                'fail_url': settings.SSLCOMMERZ_FAIL_URL,
                'cancel_url': settings.SSLCOMMERZ_CANCEL_URL,
                'emi_option': 0,
                'cus_name': cus_name,
                'cus_email': order.buyer.email or 'customer@example.com',
                'cus_phone': getattr(order.buyer, 'phone_number', None) or '01700000000',
                'cus_add1': order.shipping_address,
                'cus_city': order.shipping_city,
                'cus_state': order.shipping_state,
                'cus_postcode': order.shipping_postal_code,
                'cus_country': order.shipping_country,
                'shipping_method': 'NO',
                'product_name': order.item_name,
                'product_category': 'marketplace',
                'product_profile': 'general',
            }
            
            # Make request to SSL Commerz
            response = requests.post(self.api_url, data=payload, timeout=10)
            response.raise_for_status()
            
            # Parse response
            result = self._parse_response(response.text)
            
            if result.get('status') == 'SUCCESS':
                # Store gateway transaction ID
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment.gateway_response = result
                    payment.save()
                
                return {
                    'success': True,
                    'gateway_url': result.get('GatewayPageURL'),
                    'session_id': result.get('sessionkey'),
                    'message': 'Payment session initiated successfully'
                }
            else:
                return {
                    'success': False,
                    'error': result.get('failedreason', 'Payment initiation failed'),
                    'message': 'Failed to initiate payment'
                }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Network error while initiating payment'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error initiating payment'
            }
    
    def validate_payment(self, transaction_id):
        """
        Validate payment with SSL Commerz
        
        Args:
            transaction_id (str): SSL Commerz transaction ID
            
        Returns:
            dict: Validation result
        """
        try:
            payload = {
                'store_id': self.store_id,
                'store_passwd': self.store_password,
                'ref_id': transaction_id,
            }
            
            response = requests.post(self.validation_url, data=payload, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response
            result = response.json()
            
            return {
                'success': True,
                'data': result,
                'status': result.get('status', 'UNKNOWN')
            }
        
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Network error while validating payment'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error validating payment'
            }
    
    def handle_payment_success(self, request_data):
        """
        Handle successful payment callback from SSL Commerz
        
        Args:
            request_data (dict): POST data from SSL Commerz callback
            
        Returns:
            dict: Processing result
        """
        try:
            tran_id = request_data.get('tran_id')
            val_id = request_data.get('val_id')
            status = request_data.get('status')
            
            # Find order by transaction ID
            try:
                order = Order.objects.get(order_number=tran_id)
            except Order.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Order not found',
                    'message': 'Invalid transaction ID'
                }
            
            # Validate payment with SSL Commerz
            validation = self.validate_payment(val_id)
            
            if validation['success'] and validation['status'] == 'VALID':
                # Update payment record
                payment = Payment.objects.filter(order=order).first()
                if payment:
                    payment.status = 'completed'
                    payment.transaction_id = val_id
                    payment.gateway_response = request_data
                    payment.processed_at = timezone.now()
                    payment.save()
                    
                    # Update order status
                    order.mark_as_confirmed()
                    
                    return {
                        'success': True,
                        'message': 'Payment processed successfully',
                        'order_id': str(order.id),
                        'transaction_id': val_id
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Payment record not found',
                        'message': 'Unable to update payment'
                    }
            else:
                return {
                    'success': False,
                    'error': 'Payment validation failed',
                    'message': 'SSL Commerz validation failed'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Error processing payment success'
            }
    
    def handle_payment_fail(self, request_data):
        """
        Handle failed payment callback from SSL Commerz
        
        Args:
            request_data (dict): POST data from SSL Commerz callback
            
        Returns:
            dict: Processing result
        """
        try:
            tran_id = request_data.get('tran_id')
            error_message = request_data.get('error_description', 'Payment failed')
            
            # Find order
            try:
                order = Order.objects.get(order_number=tran_id)
            except Order.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Order not found'
                }
            
            # Update payment record
            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment.status = 'failed'
                payment.error_message = error_message
                payment.gateway_response = request_data
                payment.save()
            
            return {
                'success': True,
                'message': 'Payment failure recorded',
                'error': error_message
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_payment_cancel(self, request_data):
        """
        Handle cancelled payment callback from SSL Commerz
        
        Args:
            request_data (dict): POST data from SSL Commerz callback
            
        Returns:
            dict: Processing result
        """
        try:
            tran_id = request_data.get('tran_id')
            
            # Find order
            try:
                order = Order.objects.get(order_number=tran_id)
            except Order.DoesNotExist:
                return {
                    'success': False,
                    'error': 'Order not found'
                }
            
            # Update payment record
            payment = Payment.objects.filter(order=order).first()
            if payment:
                payment.status = 'cancelled'
                payment.gateway_response = request_data
                payment.save()
            
            return {
                'success': True,
                'message': 'Payment cancellation recorded'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _parse_response(response_text):
        """
        Parse SSL Commerz response
        
        Args:
            response_text (str): Response text from SSL Commerz
            
        Returns:
            dict: Parsed response
        """
        try:
            # Try to parse as JSON first
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Parse as form data if JSON fails
            result = {}
            for line in response_text.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    result[key.strip()] = value.strip()
            return result
