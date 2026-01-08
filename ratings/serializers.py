from rest_framework import serializers
from ratings.models import Review, Rating, ReviewHelpfulness
from users.api.serializers import UserListSerializer


class ReviewHelpfulnessSerializer(serializers.ModelSerializer):
    """Serializer for review helpfulness votes."""
    
    class Meta:
        model = ReviewHelpfulness
        fields = ['id', 'vote_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviews."""
    
    reviewer = UserListSerializer(read_only=True)
    user_vote = serializers.SerializerMethodField()
    
    class Meta:
        model = Review
        fields = [
            'id', 'reviewer', 'title', 'text', 'rating', 'communication_rating',
            'item_accuracy_rating', 'shipping_rating', 'is_verified_purchase',
            'helpful_count', 'unhelpful_count', 'is_approved', 'is_flagged',
            'seller_response', 'seller_response_date', 'created_at', 'updated_at',
            'user_vote'
        ]
        read_only_fields = [
            'id', 'reviewer', 'helpful_count', 'unhelpful_count', 'is_approved',
            'is_flagged', 'seller_response', 'seller_response_date', 'created_at',
            'updated_at'
        ]
    
    def get_user_vote(self, obj):
        """Get current user's vote on this review."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        vote = obj.helpfulness_votes.filter(user=request.user).first()
        if vote:
            return vote.vote_type
        return None


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reviews."""
    
    class Meta:
        model = Review
        fields = [
            'title', 'text', 'rating', 'communication_rating',
            'item_accuracy_rating', 'shipping_rating'
        ]
    
    def create(self, validated_data):
        """Create review with reviewer from request user."""
        validated_data['reviewer'] = self.context['request'].user
        validated_data['seller'] = self.context['seller']
        return super().create(validated_data)


class RatingSerializer(serializers.ModelSerializer):
    """Serializer for seller ratings."""
    
    seller = UserListSerializer(read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'seller', 'average_rating', 'total_reviews',
            'five_star_count', 'four_star_count', 'three_star_count',
            'two_star_count', 'one_star_count', 'average_communication',
            'average_item_accuracy', 'average_shipping'
        ]
        read_only_fields = [
            'id', 'seller', 'average_rating', 'total_reviews',
            'five_star_count', 'four_star_count', 'three_star_count',
            'two_star_count', 'one_star_count', 'average_communication',
            'average_item_accuracy', 'average_shipping'
        ]


class SellerReviewSummarySerializer(serializers.Serializer):
    """Serializer for seller review summary."""
    
    seller_id = serializers.UUIDField()
    seller_name = serializers.CharField()
    average_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    total_reviews = serializers.IntegerField()
    recent_reviews = ReviewSerializer(many=True)
    rating_distribution = serializers.DictField()
