# Backend Testing Guide

## Overview
Comprehensive test suite for the CarCo MVP Backend covering all apps.

## Test Structure

```
mvpBackend/
├── users/
│   └── tests.py (✅ Existing + Enhanced)
├── cars/
│   └── tests.py (✅ Created)
├── parts/
│   └── tests.py (✅ Created)
├── forum/
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py (✅ Created)
│       └── test_views.py (✅ Created)
├── payments/
│   └── tests.py (✅ Created)
├── messaging/
│   └── tests.py (✅ Created)
├── locations/
│   └── tests.py (✅ Created)
├── comments/
│   └── tests.py (✅ Created)
├── ratings/
│   └── tests.py (✅ Created)
├── notifications/
│   └── tests.py (✅ Created)
├── integration_tests.py (✅ Created)
└── run_tests.py (✅ Created)
```

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Tests for Specific App
```bash
python run_tests.py forum
python run_tests.py cars
python run_tests.py payments
```

### Run with Coverage Report
```bash
python run_tests.py --coverage
```

### Run Specific Test Class
```bash
python manage.py test forum.tests.test_models.ForumThreadModelTest
```

### Run Specific Test Method
```bash
python manage.py test forum.tests.test_models.ForumThreadModelTest.test_thread_creation
```

### Run Integration Tests
```bash
python manage.py test integration_tests
```

## Test Coverage

### Unit Tests by App

#### 1. **Users App**
- CustomUser model creation
- Superuser creation
- Email validation
- Profile picture handling
- Unique email constraint

#### 2. **Cars App**
- Car listing creation
- Car image management
- Car specifications
- Status management (active, sold, pending)
- Seller relationship

#### 3. **Parts App**
- Part category hierarchy
- Company store management
- Part listing with compatibility
- Part reviews and ratings
- Review voting system

#### 4. **Forum App**
- Forum categories
- Thread creation and management
- Response system
- Expert verification
- Voting on responses
- Thread resolution

#### 5. **Payments App**
- Order creation and management
- Payment processing
- Invoice generation
- Refund handling
- Wallet system
- Discount codes

#### 6. **Messaging App**
- Conversation creation (direct, group)
- Message sending
- Message attachments
- Read receipts
- User blocking

#### 7. **Locations App**
- Shop location management
- Location types (shop, service, warehouse)
- Approval workflow
- Operating hours
- Geographic coordinates

#### 8. **Comments App**
- Generic comments on cars/parts
- Nested replies
- Like system
- Moderation (approval, flagging)

#### 9. **Ratings App**
- Seller reviews
- Aggregated seller ratings
- Review helpfulness voting
- Verified purchase reviews

#### 10. **Notifications App**
- Notification creation
- Notification types
- Read/unread status
- Notification preferences
- Quiet hours

### Integration Tests
- **User Workflow**: Registration → Listing → Comments
- **Marketplace Workflow**: Browse → Purchase → Payment → Review
- **Forum Workflow**: Create Thread → Responses → Resolution
- **Messaging Workflow**: Conversation → Messages → Read Receipts
- **Company Store Workflow**: Store Setup → Parts Listing
- **Wallet Workflow**: Order → Payment → Wallet Update

## Coverage Goals
- **Target**: 80%+ code coverage
- **Current**: Run `python run_tests.py --coverage` to check

## Writing New Tests

### Model Test Template
```python
from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class MyModelTest(TestCase):
    def setUp(self):
        # Setup test data
        pass
    
    def test_model_creation(self):
        # Test model creation
        pass
    
    def test_model_str_representation(self):
        # Test __str__ method
        pass
```

### API Test Template
```python
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

class MyAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(...)
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_list_endpoint(self):
        response = self.client.get('/api/endpoint/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
```

## Best Practices

1. **Isolate Tests**: Each test should be independent
2. **Use setUp**: Initialize common test data in setUp method
3. **Clear Names**: Use descriptive test method names
4. **Test Edge Cases**: Test both success and failure scenarios
5. **Mock External Services**: Don't hit real APIs in tests
6. **Database**: Tests use a separate test database (auto-cleaned)

## Continuous Integration

For CI/CD pipeline, add to `.github/workflows/tests.yml`:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --coverage
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all apps are in `INSTALLED_APPS`
2. **Database Errors**: Tests create a temporary test database
3. **Authentication**: Use JWT tokens for authenticated endpoints
4. **Foreign Keys**: Create related objects in setUp

### Debug Mode
```bash
python manage.py test --debug-mode
python manage.py test --verbosity=2
```

## Next Steps

1. Run all tests: `python run_tests.py`
2. Check coverage: `python run_tests.py --coverage`
3. Fix any failing tests
4. Add tests for new features
5. Maintain 80%+ coverage
