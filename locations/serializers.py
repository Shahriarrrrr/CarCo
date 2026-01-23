from rest_framework import serializers
from .models import ShopLocation


class ShopLocationSerializer(serializers.ModelSerializer):
    """Serializer for shop locations with detailed information."""
    
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    seller_email = serializers.EmailField(source='seller.email', read_only=True)
    store_name = serializers.CharField(source='store.store_name', read_only=True, allow_null=True)
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    approval_status_display = serializers.CharField(source='get_approval_status_display', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True, allow_null=True)
    
    class Meta:
        model = ShopLocation
        fields = [
            'id', 'seller', 'seller_name', 'seller_email', 'store', 'store_name',
            'name', 'location_type', 'location_type_display', 'description',
            'latitude', 'longitude', 'address', 'city', 'state', 'postal_code', 'country',
            'phone', 'email', 'website', 'operating_hours', 'image',
            'approval_status', 'approval_status_display', 'is_active',
            'admin_notes', 'created_at', 'updated_at', 'approved_at', 
            'approved_by', 'approved_by_name'
        ]
        read_only_fields = [
            'id', 'seller', 'approval_status', 'approved_at', 'approved_by',
            'created_at', 'updated_at', 'admin_notes'
        ]
    
    def validate(self, data):
        """Validate location data."""
        # Validate coordinates
        if 'latitude' in data and not (-90 <= float(data['latitude']) <= 90):
            raise serializers.ValidationError({
                'latitude': 'Latitude must be between -90 and 90'
            })
        
        if 'longitude' in data and not (-180 <= float(data['longitude']) <= 180):
            raise serializers.ValidationError({
                'longitude': 'Longitude must be between -180 and 180'
            })
        
        return data


class ShopLocationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating shop locations."""
    
    # Override website field to allow blank/empty strings
    website = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    
    class Meta:
        model = ShopLocation
        fields = [
            'store', 'name', 'location_type', 'description',
            'latitude', 'longitude', 'address', 'city', 'state', 
            'postal_code', 'country', 'phone', 'email', 'website',
            'operating_hours', 'image'
        ]
    
    def validate_website(self, value):
        """Allow empty string for website and auto-fix URLs without protocol."""
        if value == '' or value is None:
            return None
        
        # If URL doesn't start with http:// or https://, add https://
        if value and not value.startswith(('http://', 'https://')):
            value = f'https://{value}'
        
        return value
    
    def validate_email(self, value):
        """Allow empty string for email."""
        if value == '' or value is None:
            return None
        return value
    
    def validate(self, data):
        """Validate location data."""
        # Clean up empty strings
        if 'website' in data and data['website'] == '':
            data['website'] = None
        if 'email' in data and data['email'] == '':
            data['email'] = None
            
        # Validate coordinates
        if not (-90 <= float(data['latitude']) <= 90):
            raise serializers.ValidationError({
                'latitude': 'Latitude must be between -90 and 90'
            })
        
        if not (-180 <= float(data['longitude']) <= 180):
            raise serializers.ValidationError({
                'longitude': 'Longitude must be between -180 and 180'
            })
        
        return data


class ShopLocationPublicSerializer(serializers.ModelSerializer):
    """Serializer for public map display - minimal information."""
    
    location_type_display = serializers.CharField(source='get_location_type_display', read_only=True)
    lat = serializers.DecimalField(source='latitude', max_digits=10, decimal_places=8, read_only=True)
    lng = serializers.DecimalField(source='longitude', max_digits=11, decimal_places=8, read_only=True)
    type = serializers.CharField(source='location_type', read_only=True)
    hours = serializers.CharField(source='operating_hours', read_only=True)
    
    class Meta:
        model = ShopLocation
        fields = [
            'id', 'name', 'type', 'location_type_display',
            'lat', 'lng', 'address', 'city', 'phone',
            'hours', 'image'
        ]
