from rest_framework import serializers
from comments.models import Comment, CommentReply, CommentLike
from users.api.serializers import UserListSerializer


class CommentLikeSerializer(serializers.ModelSerializer):
    """Serializer for comment likes."""
    
    class Meta:
        model = CommentLike
        fields = ['id', 'like_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class CommentReplySerializer(serializers.ModelSerializer):
    """Serializer for comment replies."""
    
    author = UserListSerializer(read_only=True)
    user_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentReply
        fields = [
            'id', 'author', 'text', 'likes_count', 'is_approved',
            'is_flagged', 'created_at', 'updated_at', 'user_liked'
        ]
        read_only_fields = [
            'id', 'author', 'likes_count', 'is_approved', 'is_flagged',
            'created_at', 'updated_at'
        ]
    
    def get_user_liked(self, obj):
        """Check if current user liked this reply."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return CommentLike.objects.filter(
            user=request.user,
            reply=obj,
            like_type='reply'
        ).exists()


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""
    
    author = UserListSerializer(read_only=True)
    replies = CommentReplySerializer(many=True, read_only=True)
    user_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'text', 'likes_count', 'replies_count',
            'is_approved', 'is_flagged', 'replies', 'created_at',
            'updated_at', 'user_liked'
        ]
        read_only_fields = [
            'id', 'author', 'likes_count', 'replies_count', 'is_approved',
            'is_flagged', 'created_at', 'updated_at'
        ]
    
    def get_user_liked(self, obj):
        """Check if current user liked this comment."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return CommentLike.objects.filter(
            user=request.user,
            comment=obj,
            like_type='comment'
        ).exists()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""
    
    class Meta:
        model = Comment
        fields = ['text']
    
    def create(self, validated_data):
        """Create comment with author from request user."""
        validated_data['author'] = self.context['request'].user
        validated_data['content_type'] = self.context['content_type']
        validated_data['object_id'] = self.context['object_id']
        return super().create(validated_data)


class CommentReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comment replies."""
    
    class Meta:
        model = CommentReply
        fields = ['text']
    
    def create(self, validated_data):
        """Create reply with author from request user."""
        validated_data['author'] = self.context['request'].user
        validated_data['comment'] = self.context['comment']
        return super().create(validated_data)
