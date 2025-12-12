
from django.test import TestCase
from django.core.exceptions import ValidationError
from users.models import CustomUser
import uuid

class CustomUserModelTest(TestCase):
	def setUp(self):
		self.email = 'testuser@example.com'
		self.password = 'testpass123'
		self.user = CustomUser.objects.create_user(
			email=self.email,
			password=self.password,
			first_name='Test',
			last_name='User',
			date_of_birth='1990-01-01'
		)

	def test_create_user(self):
		self.assertEqual(self.user.email, self.email)
		self.assertTrue(self.user.check_password(self.password))
		self.assertEqual(self.user.first_name, 'Test')
		self.assertEqual(self.user.last_name, 'User')
		self.assertTrue(isinstance(self.user.id, uuid.UUID))
		self.assertTrue(self.user.is_active)
		self.assertFalse(self.user.is_staff)
		self.assertIsNotNone(self.user.date_joined)

	def test_create_superuser(self):
		superuser = CustomUser.objects.create_superuser(
			email='admin@example.com',
			password='adminpass123'
		)
		self.assertTrue(superuser.is_staff)
		self.assertTrue(superuser.is_superuser)
		self.assertTrue(superuser.check_password('adminpass123'))

	def test_email_is_required(self):
		with self.assertRaises(ValueError):
			CustomUser.objects.create_user(email=None, password='nopass')

	def test_str_method(self):
		self.assertEqual(str(self.user), self.email)

	def test_profile_picture_blank(self):
		self.assertFalse(self.user.profile_picture)

	def test_unique_email(self):
		with self.assertRaises(Exception):
			CustomUser.objects.create_user(
				email=self.email,
				password='anotherpass'
			)

	def test_date_of_birth_blank(self):
		user = CustomUser.objects.create_user(
			email='dobblank@example.com',
			password='testpass'
		)
		self.assertIsNone(user.date_of_birth)
	# Create your tests here.
