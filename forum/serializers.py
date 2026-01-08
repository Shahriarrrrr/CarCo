from rest_framework import serializers
from forum.models import (
    ForumCategory, ForumThread, ForumResponse, ExpertVerification, ResponseVote
)
from users.api.serializers import UserListSerializer


class ForumCategorySerializer(serializers.ModelSerializer):
    """Serializer for forum categories."""
    
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'description', 'icon', 'is_active']
        read_only_fields = ['id']


class ExpertVerificationSerializer(serializers.ModelSerializer):
    """Serializer for expert verification."""
    
    user = UserListSerializer(read_only=True)
    helpfulness_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ExpertVerification
        fields = [
            'id', 'user', 'expertise_areas', 'years_of_experience', 'bio',
            'status', 'helpful_responses', 'total_responses', 'helpfulness_rate',
            'verified_at'
        ]
        read_only_fields = ['id', 'user', 'status', 'helpful_responses', 'total_responses', 'verified_at']
    
    def get_helpfulness_rate(self, obj):
        """Get helpfulness rate."""
        return obj.get_helpfulness_rate()


class ResponseVoteSerializer(serializers.ModelSerializer):
    """Serializer for response votes."""
    
    class Meta:
        model = ResponseVote
        fields = ['id', 'vote_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class ForumResponseSerializer(serializers.ModelSerializer):
    """Serializer for forum responses."""
    
    author = UserListSerializer(read_only=True)
    is_expert = serializers.SerializerMethodField()
    user_vote = serializers.SerializerMethodField()
    helpfulness_score = serializers.SerializerMethodField()
    
    class Meta:
        model = ForumResponse
        fields = [
            'id', 'author', 'content', 'is_expert_response', 'is_ai_response',
            'ai_confidence', 'helpful_count', 'unhelpful_count', 'is_approved',
            'is_flagged', 'created_at', 'updated_at', 'is_expert', 'user_vote',
            'helpfulness_score'
        ]
        read_only_fields = [
            'id', 'author', 'is_approved', 'is_flagged', 'helpful_count',
            'unhelpful_count', 'created_at', 'updated_at'
        ]
    
    def get_is_expert(self, obj):
        """Check if author is verified expert."""
        return hasattr(obj.author, 'expert_verification') and \
               obj.author.expert_verification.status == 'approved'
    
    def get_user_vote(self, obj):
        """Get current user's vote on this response."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        vote = obj.votes.filter(user=request.user).first()
        if vote:
            return vote.vote_type
        return None
    
    def get_helpfulness_score(self, obj):
        """Get helpfulness score."""
        return obj.get_helpfulness_score()


class ForumThreadListSerializer(serializers.ModelSerializer):
    """Serializer for forum thread list view."""
    
    author = UserListSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    
    class Meta:
        model = ForumThread
        fields = [
            'id', 'author', 'category', 'title', 'car_make', 'car_model',
            'car_year', 'status', 'is_pinned', 'is_featured', 'views_count',
            'responses_count', 'created_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'author', 'views_count', 'responses_count', 'created_at', 'resolved_at'
        ]


class ForumThreadDetailSerializer(serializers.ModelSerializer):
    """Serializer for forum thread detail view."""
    
    author = UserListSerializer(read_only=True)
    category = ForumCategorySerializer(read_only=True)
    responses = ForumResponseSerializer(many=True, read_only=True)
    
    class Meta:
        model = ForumThread
        fields = [
            'id', 'author', 'category', 'title', 'description', 'car_make',
            'car_model', 'car_year', 'status', 'is_pinned', 'is_featured',
            'views_count', 'responses_count', 'responses', 'created_at',
            'updated_at', 'resolved_at'
        ]
        read_only_fields = [
            'id', 'author', 'views_count', 'responses_count', 'created_at',
            'updated_at', 'resolved_at'
        ]


class ForumThreadCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating forum threads."""
    
    class Meta:
        model = ForumThread
        fields = [
            'category', 'title', 'description', 'car_make', 'car_model', 'car_year'
        ]
    
    def create(self, validated_data):
        """Create thread with author from request user."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ForumResponseCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating forum responses."""
    
    class Meta:
        model = ForumResponse
        fields = ['content']
    
    def create(self, validated_data):
        """Create response with author from request user."""
        validated_data['author'] = self.context['request'].user
        validated_data['thread'] = self.context['thread']
        return super().create(validated_data)


class ExpertVerificationRequestSerializer(serializers.ModelSerializer):
    """Serializer for requesting expert verification."""
    
    class Meta:
        model = ExpertVerification
        fields = ['expertise_areas', 'years_of_experience', 'bio', 'verification_document']
