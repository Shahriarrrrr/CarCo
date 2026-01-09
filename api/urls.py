from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.api.views import UserViewSet
from cars.views import CarViewSet
from parts.views import CarPartViewSet, PartCategoryViewSet, CompanyStoreViewSet
from forum.views import ForumThreadViewSet, ForumResponseViewSet, ExpertVerificationViewSet, ForumCategoryViewSet
from comments.views import CommentViewSet, CommentReplyViewSet
from ratings.views import ReviewViewSet, SellerRatingViewSet
from notifications.views import NotificationViewSet, NotificationPreferenceViewSet
from messaging.views import ConversationViewSet, MessageViewSet, BlockedUserViewSet
from payments.views import OrderViewSet, PaymentViewSet, InvoiceViewSet, RefundViewSet, WalletViewSet, DiscountViewSet

# Create unified router and register all viewsets
router = DefaultRouter()

# Users
router.register(r'users', UserViewSet, basename='user')

# Cars
router.register(r'cars', CarViewSet, basename='car')

# Parts
router.register(r'parts', CarPartViewSet, basename='part')
router.register(r'part-categories', PartCategoryViewSet, basename='part-category')
router.register(r'company-stores', CompanyStoreViewSet, basename='company-store')

# Forum
router.register(r'forum/categories', ForumCategoryViewSet, basename='forum-category')
router.register(r'forum/threads', ForumThreadViewSet, basename='forum-thread')
router.register(r'forum/responses', ForumResponseViewSet, basename='forum-response')
router.register(r'forum/experts', ExpertVerificationViewSet, basename='expert-verification')

# Comments
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'comment-replies', CommentReplyViewSet, basename='comment-reply')

# Ratings
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'seller-ratings', SellerRatingViewSet, basename='seller-rating')

# Notifications
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'notification-preferences', NotificationPreferenceViewSet, basename='notification-preference')

# Messaging
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'blocked-users', BlockedUserViewSet, basename='blocked-user')

# Payments
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'refunds', RefundViewSet, basename='refund')
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'discounts', DiscountViewSet, basename='discount')

urlpatterns = [
    path('', include(router.urls)),
]
