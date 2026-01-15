from rest_framework import serializers
from parts.models import CarPart, PartImage, PartCategory, PartCompatibility, CompanyStore
from users.api.serializers import UserListSerializer


class PartCategorySerializer(serializers.ModelSerializer):
    """Serializer for part categories."""
    
    class Meta:
        model = PartCategory
        fields = ['id', 'name', 'description', 'icon', 'parent_category']
        read_only_fields = ['id']


class PartImageSerializer(serializers.ModelSerializer):
    """Serializer for part images."""
    
    class Meta:
        model = PartImage
        fields = ['id', 'image', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class PartCompatibilitySerializer(serializers.ModelSerializer):
    """Serializer for part compatibility."""
    
    class Meta:
        model = PartCompatibility
        fields = ['id', 'car_make', 'car_model', 'car_year_from', 'car_year_to', 'notes']
        read_only_fields = ['id']


class CompanyStoreSerializer(serializers.ModelSerializer):
    """Serializer for company stores."""
    
    company = UserListSerializer(read_only=True)
    
    class Meta:
        model = CompanyStore
        fields = [
            'id', 'company', 'store_name', 'store_description', 'store_logo',
            'store_banner', 'store_email', 'store_phone', 'store_website',
            'store_address', 'store_city', 'store_state', 'store_country',
            'store_rating', 'total_reviews', 'is_verified', 'is_active'
        ]
        read_only_fields = ['id', 'company', 'store_rating', 'total_reviews']


class PartListSerializer(serializers.ModelSerializer):
    """Serializer for part list view."""
    
    seller = UserListSerializer(read_only=True)
    category = PartCategorySerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = CarPart
        fields = [
            'id', 'seller', 'category', 'name', 'brand', 'price',
            'condition', 'quantity_in_stock', 'status', 'rating',
            'reviews_count', 'is_featured', 'created_at', 'primary_image'
        ]
        read_only_fields = ['id', 'created_at', 'status', 'rating', 'reviews_count']
    
    def get_primary_image(self, obj):
        """Get primary image URL."""
        image = obj.images.filter(is_primary=True).first() or obj.images.first()
        if image:
            return PartImageSerializer(image).data
        return None


class PartDetailSerializer(serializers.ModelSerializer):
    """Serializer for part detail view."""
    
    seller = UserListSerializer(read_only=True)
    category = PartCategorySerializer(read_only=True)
    images = PartImageSerializer(many=True, read_only=True)
    compatibilities = PartCompatibilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = CarPart
        fields = [
            'id', 'seller', 'category', 'name', 'description', 'part_number',
            'condition', 'brand', 'model', 'price', 'quantity_in_stock',
            'quantity_sold', 'status', 'is_featured', 'warranty_months',
            'warranty_description', 'weight', 'dimensions', 'rating',
            'reviews_count', 'images', 'compatibilities', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'rating', 'reviews_count', 'quantity_sold']


class PartCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating parts."""
    
    class Meta:
        model = CarPart
        fields = [
            'category', 'name', 'description', 'part_number', 'condition',
            'brand', 'model', 'price', 'quantity_in_stock', 'warranty_months',
            'warranty_description', 'weight', 'dimensions'
        ]
    
    def create(self, validated_data):
        """Create part with seller from request user."""
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class PartSearchSerializer(serializers.Serializer):
    """Serializer for part search filters."""
    
    name = serializers.CharField(required=False, allow_blank=True)
    category = serializers.UUIDField(required=False)
    brand = serializers.CharField(required=False, allow_blank=True)
    condition = serializers.ChoiceField(choices=CarPart.CONDITION_CHOICES, required=False)
    price_from = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    price_to = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    in_stock_only = serializers.BooleanField(required=False, default=False)
    search = serializers.CharField(required=False, allow_blank=True)
