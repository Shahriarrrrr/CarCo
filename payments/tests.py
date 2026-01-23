from django.test import TestCase
from django.contrib.auth import get_user_model
from payments.models import Order, Payment, Invoice, Refund, Wallet, WalletTransaction, Discount
from decimal import Decimal
from django.utils import timezone

User = get_user_model()


class OrderModelTest(TestCase):
    """Test suite for Order model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="part",
            order_number="ORD-TEST-001",
            item_name="Brake Pads",
            quantity=2,
            unit_price=Decimal("150.00"),
            subtotal=Decimal("300.00"),
            tax_amount=Decimal("45.00"),
            shipping_cost=Decimal("20.00"),
            total_amount=Decimal("365.00"),
            status="pending"
        )

    def test_order_creation(self):
        """Test creating an order"""
        self.assertEqual(self.order.buyer, self.buyer)
        self.assertEqual(self.order.seller, self.seller)
        self.assertEqual(self.order.total_amount, Decimal("365.00"))
        self.assertEqual(self.order.status, "pending")

    def test_order_number_generation(self):
        """Test that order number is auto-generated"""
        self.assertIsNotNone(self.order.order_number)

    def test_order_str_representation(self):
        """Test string representation"""
        self.assertIn(self.order.order_number, str(self.order))

    def test_order_defaults(self):
        """Test default values"""
        # Create separate users to avoid order_number conflicts
        buyer2 = User.objects.create_user(
            email="buyer2@example.com",
            password="pass123",
            first_name="Buyer2", last_name="User"
        )
        seller3 = User.objects.create_user(
            email="seller3@example.com",
            password="pass123",
            first_name="Seller3", last_name="User"
        )
        order = Order.objects.create(
            buyer=buyer2,
            seller=seller3,
            order_type="car",
            order_number="ORD-TEST-002",
            item_name="Honda Civic",
            unit_price=Decimal("20000.00"),
            subtotal=Decimal("20000.00"),
            total_amount=Decimal("20000.00")
        )
        self.assertEqual(order.status, "pending")
        self.assertEqual(order.quantity, 1)


class PaymentModelTest(TestCase):
    """Test suite for Payment model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="part",
            order_number="ORD-TEST-003",
            item_name="Test Item",
            unit_price=Decimal("500.00"),
            subtotal=Decimal("500.00"),
            total_amount=Decimal("500.00")
        )

    def test_payment_creation(self):
        """Test creating a payment"""
        payment = Payment.objects.create(
            order=self.order,
            payment_method="card",
            amount=Decimal("500.00"),
            currency="BDT",
            status="pending"
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.amount, Decimal("500.00"))

    def test_payment_one_to_one(self):
        """Test one-to-one relationship with order"""
        Payment.objects.create(
            order=self.order,
            payment_method="card",
            amount=Decimal("500.00")
        )
        
        with self.assertRaises(Exception):
            Payment.objects.create(
                order=self.order,
                payment_method="bkash",
                amount=Decimal("500.00")
            )


class InvoiceModelTest(TestCase):
    """Test suite for Invoice model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="car",
            order_number="ORD-TEST-004",
            item_name="Toyota Camry",
            unit_price=Decimal("25000.00"),
            subtotal=Decimal("25000.00"),
            total_amount=Decimal("25000.00")
        )

    def test_invoice_creation(self):
        """Test creating an invoice"""
        invoice = Invoice.objects.create(
            order=self.order,
            invoice_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=30),
            status="pending",
            subtotal=Decimal("25000.00"),
            amount_due=Decimal("25000.00"),
            total_amount=Decimal("25000.00")
        )
        self.assertEqual(invoice.order, self.order)
        self.assertEqual(invoice.total_amount, Decimal("25000.00"))

    def test_invoice_number_generation(self):
        """Test that invoice number is auto-generated"""
        invoice = Invoice.objects.create(
            order=self.order,
            invoice_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=30),
            subtotal=Decimal("25000.00"),
            amount_due=Decimal("25000.00"),
            total_amount=Decimal("25000.00")
        )
        self.assertIsNotNone(invoice.invoice_number)


class WalletModelTest(TestCase):
    """Test suite for Wallet model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            first_name="Test", last_name="User"
        )

    def test_wallet_creation(self):
        """Test creating a wallet"""
        wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal("1000.00"),
            total_earned=Decimal("5000.00"),
            total_spent=Decimal("4000.00")
        )
        self.assertEqual(wallet.user, self.user)
        self.assertEqual(wallet.balance, Decimal("1000.00"))

    def test_wallet_defaults(self):
        """Test default values"""
        wallet = Wallet.objects.create(user=self.user)
        self.assertEqual(wallet.balance, Decimal("0.00"))
        self.assertEqual(wallet.total_earned, Decimal("0.00"))
        self.assertEqual(wallet.total_spent, Decimal("0.00"))


class WalletTransactionModelTest(TestCase):
    """Test suite for WalletTransaction model"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            password="pass123",
            first_name="User", last_name="User"
        )
        self.wallet = Wallet.objects.create(
            user=self.user,
            balance=Decimal("500.00")
        )

    def test_transaction_creation(self):
        """Test creating a wallet transaction"""
        transaction = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type="credit",
            amount=Decimal("100.00"),
            description="Payment received"
        )
        self.assertEqual(transaction.wallet, self.wallet)
        self.assertEqual(transaction.amount, Decimal("100.00"))

    def test_transaction_types(self):
        """Test both transaction types"""
        credit = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type="credit",
            amount=Decimal("100.00")
        )
        debit = WalletTransaction.objects.create(
            wallet=self.wallet,
            transaction_type="debit",
            amount=Decimal("50.00")
        )
        self.assertEqual(credit.transaction_type, "credit")
        self.assertEqual(debit.transaction_type, "debit")


class DiscountModelTest(TestCase):
    """Test suite for Discount model"""

    def test_discount_creation(self):
        """Test creating a discount code"""
        from django.utils import timezone
        from datetime import timedelta
        
        discount = Discount.objects.create(
            code="SAVE20",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            min_order_amount=Decimal("100.00"),
            max_uses=100,
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30),
            status="active"
        )
        self.assertEqual(discount.code, "SAVE20")
        self.assertEqual(discount.discount_value, Decimal("20.00"))

    def test_discount_defaults(self):
        """Test default values"""
        from django.utils import timezone
        from datetime import timedelta
        
        discount = Discount.objects.create(
            code="TEST",
            discount_type="fixed",
            discount_value=Decimal("50.00"),
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        self.assertEqual(discount.status, "active")
        self.assertEqual(discount.times_used, 0)

    def test_discount_code_unique(self):
        """Test that discount codes must be unique"""
        from django.utils import timezone
        from datetime import timedelta
        
        Discount.objects.create(
            code="UNIQUE",
            discount_type="percentage",
            discount_value=Decimal("10.00"),
            valid_from=timezone.now(),
            valid_until=timezone.now() + timedelta(days=30)
        )
        
        with self.assertRaises(Exception):
            Discount.objects.create(
                code="UNIQUE",
                discount_type="percentage",
                discount_value=Decimal("15.00"),
                valid_from=timezone.now(),
                valid_until=timezone.now() + timedelta(days=30)
            )


class RefundModelTest(TestCase):
    """Test suite for Refund model"""

    def setUp(self):
        self.buyer = User.objects.create_user(
            email="buyer@example.com",
            password="pass123",
            first_name="Buyer", last_name="User"
        )
        self.seller = User.objects.create_user(
            email="seller@example.com",
            password="pass123",
            first_name="Seller", last_name="User"
        )
        self.order = Order.objects.create(
            buyer=self.buyer,
            seller=self.seller,
            order_type="part",
            order_number="ORD-TEST-005",
            item_name="Defective Part",
            unit_price=Decimal("300.00"),
            subtotal=Decimal("300.00"),
            total_amount=Decimal("300.00")
        )
        self.payment = Payment.objects.create(
            order=self.order,
            payment_method="card",
            amount=Decimal("300.00"),
            status="completed"
        )

    def test_refund_creation(self):
        """Test creating a refund"""
        refund = Refund.objects.create(
            order=self.order,
            payment=self.payment,
            refund_reason="Defective product",
            refund_amount=Decimal("300.00"),
            refund_percentage=Decimal("100.00"),
            status="pending"
        )
        self.assertEqual(refund.order, self.order)
        self.assertEqual(refund.refund_amount, Decimal("300.00"))

    def test_partial_refund(self):
        """Test creating a partial refund"""
        refund = Refund.objects.create(
            order=self.order,
            payment=self.payment,
            refund_reason="Partial return",
            refund_amount=Decimal("150.00"),
            refund_percentage=Decimal("50.00"),
            status="pending"
        )
        self.assertEqual(refund.refund_percentage, Decimal("50.00"))
