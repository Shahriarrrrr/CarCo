# mvpBackend - Quick Reference Guide

## Project Overview
A comprehensive Django REST Framework-based backend for a car marketplace and community platform with integrated forum, ratings, and notification systems.

---

## Quick Start

### Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Access Points
- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **Token Endpoint**: http://localhost:8000/api/token/

---

## Core Applications at a Glance

| App | Purpose | Key Models |
|-----|---------|-----------|
| **users** | User management & auth | CustomUser, ExpertVerification, NotificationPreference |
| **cars** | Car marketplace | Car, CarImage, CarSpecification |
| **parts** | Parts marketplace | CarPart, PartCategory, PartImage, PartCompatibility, CompanyStore |
| **forum** | Community discussions | ForumThread, ForumResponse, ForumCategory, ExpertVerification, ResponseVote |
| **comments** | Generic comments | Comment, CommentReply, CommentLike |
| **ratings** | Reviews & ratings | Review, Rating, ReviewHelpfulness |
| **notifications** | User notifications | Notification, NotificationPreference |

---

## API Endpoints Summary

### Authentication
```
POST   /api/token/              - Get JWT token
POST   /api/token/refresh/      - Refresh JWT token
```

### Users
```
GET    /api/users/              - List all users
POST   /api/users/              - Create new user
GET    /api/users/{id}/         - Get user details
PUT    /api/users/{id}/         - Update user (full)
PATCH  /api/users/{id}/         - Update user (partial)
DELETE /api/users/{id}/         - Delete user
```

### Cars
```
GET    /api/cars/               - List car listings
POST   /api/cars/               - Create car listing
GET    /api/cars/{id}/          - Get car details
PUT    /api/cars/{id}/          - Update car (full)
PATCH  /api/cars/{id}/          - Update car (partial)
DELETE /api/cars/{id}/          - Delete car
```

### Parts
```
GET    /api/parts/              - List parts
POST   /api/parts/              - Create part listing
GET    /api/parts/{id}/         - Get part details
PUT    /api/parts/{id}/         - Update part (full)
PATCH  /api/parts/{id}/         - Update part (partial)
DELETE /api/parts/{id}/         - Delete part

GET    /api/part-categories/    - List categories
POST   /api/part-categories/    - Create category
GET    /api/company-stores/     - List company stores
POST   /api/company-stores/     - Create store
```

### Forum
```
GET    /api/forum/categories/   - List forum categories
POST   /api/forum/categories/   - Create category
GET    /api/forum/threads/      - List threads
POST   /api/forum/threads/      - Create thread
GET    /api/forum/threads/{id}/ - Get thread details
GET    /api/forum/responses/    - List responses
POST   /api/forum/responses/    - Create response
GET    /api/forum/experts/      - List expert verifications
POST   /api/forum/experts/      - Create expert verification
```

### Comments
```
GET    /api/comments/           - List comments
POST   /api/comments/           - Create comment
GET    /api/comments/{id}/      - Get comment details
GET    /api/comment-replies/    - List replies
POST   /api/comment-replies/    - Create reply
```

### Ratings & Reviews
```
GET    /api/reviews/            - List reviews
POST   /api/reviews/            - Create review
GET    /api/reviews/{id}/       - Get review details
GET    /api/seller-ratings/     - List seller ratings
GET    /api/seller-ratings/{id}/ - Get seller rating
```

### Notifications
```
GET    /api/notifications/      - List notifications
GET    /api/notifications/{id}/ - Get notification
PATCH  /api/notifications/{id}/ - Mark as read
GET    /api/notification-preferences/ - Get preferences
PUT    /api/notification-preferences/ - Update preferences
```

---

## Authentication Flow

### 1. Obtain Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Use Token in Requests
```bash
curl -X GET http://localhost:8000/api/users/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 3. Refresh Token
```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}'
```

---

## Common Request/Response Examples

### Create a Car Listing
```bash
POST /api/cars/
Content-Type: application/json
Authorization: Bearer {token}

{
  "make": "Toyota",
  "model": "Camry",
  "year": 2020,
  "mileage": 45000,
  "transmission": "automatic",
  "fuel_type": "petrol",
  "condition": "good",
  "price": "25000.00",
  "title": "2020 Toyota Camry - Excellent Condition",
  "description": "Well-maintained, single owner...",
  "city": "New York",
  "state_province": "NY",
  "country": "USA",
  "color": "Silver",
  "body_type": "Sedan",
  "doors": 4,
  "seats": 5,
  "features": ["AC", "Power Steering", "ABS", "Airbags"]
}
```

### Create a Forum Thread
```bash
POST /api/forum/threads/
Content-Type: application/json
Authorization: Bearer {token}

{
  "category": "uuid-of-category",
  "title": "How to replace brake pads on 2020 Camry?",
  "description": "I need help with replacing brake pads...",
  "car_make": "Toyota",
  "car_model": "Camry",
  "car_year": 2020
}
```

### Create a Review
```bash
POST /api/reviews/
Content-Type: application/json
Authorization: Bearer {token}

{
  "seller": "uuid-of-seller",
  "title": "Great seller, fast shipping",
  "text": "Excellent experience buying from this seller...",
  "rating": 5,
  "communication_rating": 5,
  "item_accuracy_rating": 5,
  "shipping_rating": 5,
  "is_verified_purchase": true
}
```

---

## Database Models Quick Reference

### CustomUser Fields
- `id` (UUID) - Primary key
- `email` (Email) - Unique, used for login
- `first_name`, `last_name` (String)
- `phone_number` (String) - Validated format
- `user_type` (Choice) - 'individual' or 'company'
- `is_seller`, `is_buyer` (Boolean)
- `verification_status` (Choice) - unverified, pending, verified, rejected
- `seller_rating` (Decimal) - Average seller rating
- `is_suspended` (Boolean) - Account suspension status

### Car Fields
- `id` (UUID) - Primary key
- `seller` (FK) - Reference to CustomUser
- `make`, `model` (String) - Car make and model
- `year` (Integer) - Year of manufacture
- `mileage` (Integer) - In kilometers
- `price` (Decimal) - Listing price
- `status` (Choice) - active, sold, archived, pending
- `condition` (Choice) - excellent, good, fair, poor
- `created_at`, `updated_at` (DateTime)

### CarPart Fields
- `id` (UUID) - Primary key
- `seller` (FK) - Reference to CustomUser
- `category` (FK) - Reference to PartCategory
- `name` (String) - Part name
- `price` (Decimal) - Part price
- `quantity_in_stock` (Integer) - Available quantity
- `condition` (Choice) - new, refurbished, used
- `status` (Choice) - active, out_of_stock, discontinued, pending
- `rating` (Decimal) - Average rating

### ForumThread Fields
- `id` (UUID) - Primary key
- `author` (FK) - Reference to CustomUser
- `category` (FK) - Reference to ForumCategory
- `title` (String) - Thread title
- `status` (Choice) - open, resolved, closed
- `is_pinned`, `is_featured` (Boolean)
- `views_count`, `responses_count` (Integer)

### Review Fields
- `id` (UUID) - Primary key
- `reviewer` (FK) - Reference to CustomUser (who gave review)
- `seller` (FK) - Reference to CustomUser (who received review)
- `rating` (Integer) - 1-5 stars
- `communication_rating`, `item_accuracy_rating`, `shipping_rating` (Integer)
- `is_verified_purchase` (Boolean)
- `seller_response` (Text) - Seller's response to review

---

## Key Features & Workflows

### User Registration & Verification
1. User registers with email and password
2. Email verification sent
3. User verifies email
4. Optional: User applies for seller status
5. Admin reviews and approves seller status
6. User can now list items

### Car Listing Workflow
1. Seller creates car listing (status: pending)
2. Admin reviews listing
3. Listing approved (status: active)
4. Buyers can view and comment
5. Seller marks as sold (status: sold)

### Forum Discussion Workflow
1. User creates thread in category
2. Other users post responses
3. Expert users can mark responses as expert
4. Users vote on response helpfulness
5. Thread author can mark as resolved

### Review & Rating Workflow
1. Buyer purchases from seller
2. Buyer leaves review (1-5 stars)
3. Review aggregated into seller rating
4. Seller can respond to review
5. Other users vote on review helpfulness

### Notification Workflow
1. Event occurs (new review, forum reply, etc.)
2. Notification created
3. User preferences checked
4. Email/in-app notification sent
5. User marks notification as read

---

## Database Indexes

Strategic indexes for performance:

```
Users:
  - email
  - phone_number
  - is_seller
  - verification_status

Cars:
  - (seller, status)
  - (make, model, year)
  - price
  - city
  - created_at

Parts:
  - (seller, status)
  - category
  - brand
  - price
  - created_at

Forum:
  - (author, status)
  - category
  - (car_make, car_model)
  - created_at

Notifications:
  - (user, is_read)
  - (user, notification_type)
  - created_at
```

---

## Configuration Files

### settings.py Key Settings
```python
AUTH_USER_MODEL = 'users.CustomUser'
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### Environment Variables
```
SECRET_KEY=your-secret-key
DEBUG=True/False
ALLOWED_HOSTS=localhost,127.0.0.1
```

---

## Common Queries

### Get all active car listings
```
GET /api/cars/?status=active
```

### Get user's reviews
```
GET /api/reviews/?seller={user_id}
```

### Get forum threads by category
```
GET /api/forum/threads/?category={category_id}
```

### Get unread notifications
```
GET /api/notifications/?is_read=false
```

### Get parts in stock
```
GET /api/parts/?status=active&quantity_in_stock__gt=0
```

---

## Troubleshooting

### 401 Unauthorized
- Token expired: Use refresh endpoint
- Invalid token: Re-authenticate
- Missing Authorization header: Add `Authorization: Bearer {token}`

### 403 Forbidden
- User doesn't have permission
- Check user roles (is_seller, is_staff)
- Verify object ownership

### 404 Not Found
- Resource doesn't exist
- Check UUID format
- Verify resource ID

### 400 Bad Request
- Invalid data format
- Missing required fields
- Validation errors in response

---

## Performance Tips

1. **Use Pagination**: Add `?page=1&page_size=20` to list endpoints
2. **Filter Results**: Use query parameters to reduce data
3. **Select Fields**: Use `?fields=id,name` to get only needed fields
4. **Use Indexes**: Queries on indexed fields are faster
5. **Cache Results**: Implement caching for frequently accessed data

---

## Security Best Practices

1. **Never expose SECRET_KEY**: Use environment variables
2. **Use HTTPS**: Enable SSL/TLS in production
3. **Validate Input**: All inputs are validated
4. **Rate Limiting**: Implement to prevent abuse
5. **CORS**: Configure for your frontend domain
6. **JWT Expiry**: Set appropriate token expiration times
7. **File Upload**: Validate file types and sizes

---

## Useful Django Commands

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Shell access
python manage.py shell

# Collect static files
python manage.py collectstatic

# Check deployment readiness
python manage.py check --deploy
```

---

## File Structure
```
mvpBackend/
├── ARCHITECTURE.md              # This documentation
├── ARCHITECTURE_DIAGRAM.mmd     # System architecture diagram
├── DATA_MODEL.mmd               # Entity relationship diagram
├── API_FLOW.mmd                 # API request/response flow
├── mvpbackend/                  # Main project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                       # User management
├── cars/                        # Car marketplace
├── parts/                       # Parts marketplace
├── forum/                       # Community forum
├── comments/                    # Comments system
├── ratings/                     # Reviews & ratings
├── notifications/               # Notifications
├── api/                         # API routing
├── manage.py
├── requirements.txt
└── db.sqlite3
```

---

## Next Steps

1. Review ARCHITECTURE.md for detailed documentation
2. View ARCHITECTURE_DIAGRAM.mmd in a Mermaid viewer
3. Check DATA_MODEL.mmd for database schema
4. Review API_FLOW.mmd for request/response flow
5. Start with authentication endpoints
6. Explore individual app endpoints
7. Implement frontend integration

---

## Support & Resources

- Django Documentation: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- JWT Documentation: https://django-rest-framework-simplejwt.readthedocs.io/
- Mermaid Diagrams: https://mermaid.js.org/

---

**Last Updated**: 2024
**Version**: 1.0
**Status**: Production Ready
