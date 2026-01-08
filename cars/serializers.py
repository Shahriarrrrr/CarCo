from rest_framework import serializers
from cars.models import Car, CarImage, CarSpecification
from users.api.serializers import UserListSerializer


class CarImageSerializer(serializers.ModelSerializer):
    """Serializer for car images."""
    
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class CarSpecificationSerializer(serializers.ModelSerializer):
    """Serializer for car specifications."""
    
    class Meta:
        model = CarSpecification
        fields = [
            'id', 'horsepower', 'torque', 'acceleration_0_100', 'top_speed',
            'fuel_consumption_city', 'fuel_consumption_highway',
            'length', 'width', 'height', 'weight',
            'warranty_remaining', 'service_history'
        ]
        read_only_fields = ['id']


class CarListSerializer(serializers.ModelSerializer):
    """Serializer for car list view."""
    
    seller = UserListSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Car
        fields = [
            'id', 'seller', 'make', 'model', 'year', 'price', 'condition',
            'city', 'status', 'created_at', 'primary_image', 'mileage'
        ]
        read_only_fields = ['id', 'created_at', 'status']
    
    def get_primary_image(self, obj):
        """Get primary image URL."""
        image = obj.get_primary_image()
        if image:
            return CarImageSerializer(image).data
        return None


class CarDetailSerializer(serializers.ModelSerializer):
    """Serializer for car detail view."""
    
    seller = UserListSerializer(read_only=True)
    images = CarImageSerializer(many=True, read_only=True)
    specification = CarSpecificationSerializer(read_only=True)
    
    class Meta:
        model = Car
        fields = [
            'id', 'seller', 'make', 'model', 'year', 'mileage', 'transmission',
            'fuel_type', 'engine_capacity', 'condition', 'price', 'title',
            'description', 'city', 'state_province', 'country', 'status',
            'is_featured', 'color', 'body_type', 'doors', 'seats', 'features',
            'images', 'specification', 'created_at', 'updated_at', 'sold_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'sold_at', 'status']


class CarCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating cars."""
    
    class Meta:
        model = Car
        fields = [
            'make', 'model', 'year', 'mileage', 'transmission', 'fuel_type',
            'engine_capacity', 'condition', 'price', 'title', 'description',
            'city', 'state_province', 'country', 'color', 'body_type',
            'doors', 'seats', 'features'
        ]
    
    def create(self, validated_data):
        """Create car with seller from request user."""
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class CarSearchSerializer(serializers.Serializer):
    """Serializer for car search filters."""
    
    make = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    year_from = serializers.IntegerField(required=False)
    year_to = serializers.IntegerField(required=False)
    price_from = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    price_to = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    condition = serializers.ChoiceField(choices=Car.CONDITION_CHOICES, required=False)
    fuel_type = serializers.ChoiceField(choices=Car.FUEL_TYPE_CHOICES, required=False)
    transmission = serializers.ChoiceField(choices=Car.TRANSMISSION_CHOICES, required=False)
    city = serializers.CharField(required=False, allow_blank=True)
    mileage_max = serializers.IntegerField(required=False)
    search = serializers.CharField(required=False, allow_blank=True)
