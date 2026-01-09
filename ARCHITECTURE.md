# mvpBackend Architecture Documentation

## Overview

mvpBackend is a Django REST Framework-based backend application for a comprehensive car marketplace and community platform. It provides APIs for buying/selling cars and parts, community forums, user management, ratings, and notifications.

## Technology Stack

- **Framework**: Django 6.0
- **API**: Django REST Framework (DRF)
- **Authentication**: JWT (JSON Web Tokens) via `rest_framework_simplejwt`
- **Database**: SQLite3 (development), configurable for production
- **Language**: Python 3.x

## Project Structure

```
mvpBackend/
├── mvpbackend/          # Main project configuration
├── users/               # User management and authentication
├── cars/                # Car listings and management
├── parts/               # Car parts marketplace
├── forum/               # Community forum and discussions
├── comments/            # Comments on listings
├── ratings/             # Reviews and seller ratings
├── notifications/       # User notifications system
├── api/                 # API routing and configuration
└── manage.py            # Django management script
```

## Core Applications

### 1. **Users** (`users/`)
Handles user authentication, profiles, and account management.

**Key Models:**
- `CustomUser`: Extended Django user model with email-based authentication
  - Supports individual and company accounts
  - Verification status tracking
  - Seller/buyer role management
  - Profile information (bio, address, contact details)
  - Account suspension capabilities

**Features:**
- Email-based authentication (no username)
- UUID primary keys
- User type differentiation (individual/company)
- Seller ratings and review counts
- Account suspension with time-based lifting

---

### 2. **Cars** (`cars/`)
Manages car listings, specifications, and images.

**Key Models:**
- `Car`: Main car listing model
  - Seller relationship (ForeignKey to CustomUser)
  - Specifications (make, model, year, mileage, transmission, fuel type)
  - Pricing and condition tracking
  - Status management (active, sold, archived, pending)
  - Location information
  - Featured listing capability

- `CarImage`: Image storage for car listings
  - Multiple images per car
  - Primary image designation
  - Automatic enforcement of single primary image

- `CarSpecification`: Detailed technical specifications
  - Performance metrics (horsepower, torque, acceleration)
  - Fuel efficiency data
  - Dimensions and weight
  - Warranty and service history

**Features:**
- Comprehensive car search with multiple indexes
- Status workflow (pending → active → sold)
- Image management with primary image support
- Detailed specifications tracking

---

### 3. **Parts** (`parts/`)
Manages car parts marketplace with categories and compatibility tracking.

**Key Models:**
- `PartCategory`: Hierarchical category system
  - Parent-child category relationships
  - Category icons and descriptions

- `CarPart`: Individual part listings
  - Seller relationship
  - Category association
  - Condition tracking (new, refurbished, used)
  - Inventory management
  - Warranty information
  - Rating and review counts

- `PartImage`: Image storage for parts
  - Similar to CarImage with primary image support

- `CompanyStore`: Store profile for company sellers
  - Store branding (logo, banner)
  - Contact information
  - Location details
  - Store ratings and verification status

- `PartCompatibility`: Tracks car compatibility
  - Links parts to specific car makes/models/years
  - Compatibility notes

**Features:**
- Hierarchical category system
- Inventory tracking
- Part compatibility matrix
- Company store profiles
- Multi-image support

---

### 4. **Forum** (`forum/`)
Community discussion platform with expert verification.

**Key Models:**
- `ForumCategory`: Discussion categories
  - Active/inactive status
  - Category icons

- `ForumThread`: Discussion threads
  - Author relationship
  - Category association
  - Optional car context (make, model, year)
  - Status tracking (open, resolved, closed)
  - Pinned and featured capabilities
  - View and response counts

- `ForumResponse`: Responses to threads
  - Thread relationship
  - Author relationship
  - Expert response flagging
  - AI response support (future)
  - Helpful/unhelpful voting
  - Moderation flags

- `ExpertVerification`: Expert user tracking
  - Expertise areas (JSON)
  - Years of experience
  - Verification status
  - Helpfulness metrics

- `ResponseVote`: Voting on response helpfulness
  - Helpful/unhelpful tracking
  - Unique constraint per user-response

**Features:**
- Expert verification system
- Thread resolution tracking
- Helpful/unhelpful voting
- AI response support (future)
- Moderation capabilities

---

### 5. **Comments** (`comments/`)
Generic commenting system for cars and parts.

**Key Models:**
- `Comment`: Comments on listings
  - Generic relation to Car or CarPart
  - Author relationship
  - Engagement tracking (likes, replies)
  - Moderation flags

- `CommentReply`: Nested replies to comments
  - Comment relationship
  - Author relationship
  - Engagement tracking
  - Moderation flags

- `CommentLike`: Like tracking
  - Supports both comments and replies
  - Unique constraint per user-object

**Features:**
- Generic commenting on multiple content types
- Nested reply system
- Like tracking
- Moderation support

---

### 6. **Ratings** (`ratings/`)
Review and rating system for sellers.

**Key Models:**
- `Review`: Individual seller reviews
  - Reviewer and seller relationships
  - 1-5 star rating
  - Detailed aspect ratings (communication, accuracy, shipping)
  - Verified purchase tracking
  - Seller response capability
  - Helpful/unhelpful voting

- `Rating`: Aggregated seller ratings
  - OneToOne relationship with CustomUser
  - Average rating calculation
  - Rating distribution (1-5 stars)
  - Aspect rating averages
  - Dynamic update from reviews

- `ReviewHelpfulness`: Helpful/unhelpful votes on reviews
  - Unique constraint per user-review

**Features:**
- Detailed review system
- Aspect-based ratings
- Aggregated rating calculations
- Seller response capability
- Review helpfulness voting

---

### 7. **Notifications** (`notifications/`)
User notification system with preferences.

**Key Models:**
- `Notification`: Individual notifications
  - Multiple notification types (11 types)
  - User relationship
  - Read/unread status
  - Related object tracking
  - Action URL support

- `NotificationPreference`: User notification settings
  - OneToOne relationship with CustomUser
  - Per-type email and in-app toggles
  - Email frequency settings (instant, daily, weekly)
  - Quiet hours support

**Notification Types:**
- new_message
- listing_update
- expert_response
- review_received
- seller_response
- forum_reply
- part_available
- price_alert
- verification_status
- account_alert
- system_announcement

**Features:**
- Granular notification control
- Multiple delivery channels (email, in-app)
- Quiet hours support
- Notification frequency options

---

## API Architecture

### Authentication
- **JWT-based authentication** via `rest_framework_simplejwt`
- Endpoints:
  - `POST /api/token/` - Obtain JWT token
  - `POST /api/token/refresh/` - Refresh token

### API Endpoints Structure

All endpoints follow RESTful conventions with the following base URL: `/api/`

**Users:**
- `GET/POST /api/users/` - List/create users
- `GET/PUT/PATCH/DELETE /api/users/{id}/` - User details and management

**Cars:**
- `GET/POST /api/cars/` - List/create car listings
- `GET/PUT/PATCH/DELETE /api/cars/{id}/` - Car details and management

**Parts:**
- `GET/POST /api/parts/` - List/create parts
- `GET/POST /api/part-categories/` - Part categories
- `GET/POST /api/company-stores/` - Company store profiles

**Forum:**
- `GET/POST /api/forum/categories/` - Forum categories
- `GET/POST /api/forum/threads/` - Forum threads
- `GET/POST /api/forum/responses/` - Thread responses
- `GET/POST /api/forum/experts/` - Expert verification

**Comments:**
- `GET/POST /api/comments/` - Comments on listings
- `GET/POST /api/comment-replies/` - Comment replies

**Ratings:**
- `GET/POST /api/reviews/` - Seller reviews
- `GET /api/seller-ratings/` - Aggregated seller ratings

**Notifications:**
- `GET /api/notifications/` - User notifications
- `GET/PUT /api/notification-preferences/` - Notification settings

---

## Data Relationships

### User-Centric Relationships
```
CustomUser (1) ──→ (Many) Car [seller]
CustomUser (1) ──→ (Many) CarPart [seller]
CustomUser (1) ──→ (Many) ForumThread [author]
CustomUser (1) ──→ (Many) ForumResponse [author]
CustomUser (1) ──→ (Many) Comment [author]
CustomUser (1) ──→ (Many) Review [reviewer/seller]
CustomUser (1) ──→ (1) ExpertVerification
CustomUser (1) ──→ (1) CompanyStore
CustomUser (1) ──→ (1) NotificationPreference
CustomUser (1) ──→ (Many) Notification
```

### Content Relationships
```
Car (1) ──→ (Many) CarImage
Car (1) ──→ (1) CarSpecification
Car (1) ──→ (Many) Comment [via GenericForeignKey]

CarPart (1) ──→ (Many) PartImage
CarPart (1) ──→ (Many) PartCompatibility
CarPart (1) ──→ (Many) Comment [via GenericForeignKey]

PartCategory (1) ──→ (Many) CarPart
PartCategory (1) ──→ (Many) PartCategory [parent_category - self-referential]

ForumCategory (1) ──→ (Many) ForumThread
ForumThread (1) ──→ (Many) ForumResponse
ForumResponse (1) ──→ (Many) ResponseVote
ForumResponse (1) ──→ (Many) CommentReply [indirect]

Comment (1) ──→ (Many) CommentReply
Comment (1) ──→ (Many) CommentLike
CommentReply (1) ──→ (Many) CommentLike

Review (1) ──→ (Many) ReviewHelpfulness
Rating (1) ──→ (1) CustomUser [seller]
```

---

## Database Indexes

Strategic indexes are implemented for performance optimization:

**Users:**
- email, phone_number, is_seller, verification_status

**Cars:**
- seller + status, make + model + year, price, city, created_at

**Parts:**
- seller + status, category, brand, price, created_at

**Forum:**
- author + status, category, car_make + car_model, created_at

**Comments:**
- content_type + object_id, author, created_at

**Ratings:**
- seller + rating, reviewer, created_at

**Notifications:**
- user + is_read, user + notification_type, created_at

---

## Key Features

### 1. Multi-Role User System
- Individual buyers and sellers
- Company accounts with store profiles
- Expert verification for forum contributors
- Seller rating and review system

### 2. Marketplace Features
- Car listings with detailed specifications
- Car parts marketplace with compatibility tracking
- Company store profiles
- Image management with primary image support
- Inventory tracking for parts

### 3. Community Features
- Forum with categories and threading
- Expert verification system
- Helpful/unhelpful voting
- Moderation capabilities
- Generic commenting system

### 4. Engagement Features
- Seller reviews and ratings
- Aspect-based ratings (communication, accuracy, shipping)
- Seller response to reviews
- Comment likes and nested replies
- Response helpfulness voting

### 5. Notification System
- 11 notification types
- Email and in-app delivery
- Granular user preferences
- Quiet hours support
- Notification frequency options

### 6. Security & Verification
- Email and phone verification
- Account suspension capabilities
- Verification document upload
- Moderation flags for content
- JWT-based authentication

---

## Configuration

### Settings (`mvpbackend/settings.py`)

**Key Configurations:**
- `DEBUG`: Environment-based (default: True)
- `SECRET_KEY`: Environment-based
- `ALLOWED_HOSTS`: Environment-based
- `AUTH_USER_MODEL`: Set to `users.CustomUser`
- `REST_FRAMEWORK`: JWT authentication enabled

**Installed Apps:**
- Django core apps
- DRF (rest_framework)
- Custom apps: users, cars, parts, forum, comments, ratings, notifications

**Middleware:**
- Standard Django middleware
- Security, sessions, CSRF, authentication, messages

---

## Development Workflow

### Running the Application
```bash
python manage.py runserver
```

### Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating Admin User
```bash
python manage.py createsuperuser
```

### Admin Interface
Access at: `http://localhost:8000/admin/`

---

## Future Enhancements

1. **AI Integration**: AI-powered responses in forum
2. **Real-time Messaging**: Direct messaging between users
3. **Advanced Search**: Elasticsearch integration
4. **Payment Processing**: Stripe/PayPal integration
5. **Auction System**: Bidding on listings
6. **Wishlist**: User wishlists for cars and parts
7. **Price Alerts**: Automated price monitoring
8. **Analytics**: User behavior and marketplace analytics
9. **Mobile App**: Native mobile applications
10. **Caching**: Redis for performance optimization

---

## Security Considerations

1. **Authentication**: JWT tokens with refresh capability
2. **Authorization**: Role-based access control (buyer/seller/expert)
3. **Data Validation**: Comprehensive field validators
4. **Moderation**: Content flagging and approval system
5. **Account Security**: Suspension and verification systems
6. **File Upload**: Secure image and document uploads

---

## Performance Optimization

1. **Database Indexes**: Strategic indexes on frequently queried fields
2. **Query Optimization**: Related name usage for efficient queries
3. **Pagination**: DRF pagination for large datasets
4. **Caching**: Future Redis integration
5. **Async Tasks**: Future Celery integration for notifications

---

## Deployment Considerations

1. **Environment Variables**: Use for sensitive configuration
2. **Database**: Switch from SQLite to PostgreSQL for production
3. **Static Files**: Configure CDN for static assets
4. **Media Files**: Use cloud storage (S3, etc.)
5. **CORS**: Configure for frontend domain
6. **SSL/TLS**: Enable HTTPS
7. **Rate Limiting**: Implement API rate limiting
8. **Logging**: Comprehensive logging setup

---

## API Documentation

For detailed API documentation, refer to the DRF browsable API at:
- `http://localhost:8000/api/`

Each endpoint supports standard HTTP methods (GET, POST, PUT, PATCH, DELETE) with appropriate permissions and validations.

---

## Support & Maintenance

- Regular security updates
- Database optimization
- Performance monitoring
- User feedback integration
- Feature enhancements based on market needs
