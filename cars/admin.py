from django.contrib import admin
from cars.models import Car, CarImage, CarSpecification


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['make', 'model', 'year', 'price', 'seller', 'status', 'created_at']
    list_filter = ['status', 'condition', 'fuel_type', 'transmission', 'created_at']
    search_fields = ['make', 'model', 'title', 'seller__email']
    readonly_fields = ['id', 'created_at', 'updated_at', 'sold_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'seller', 'make', 'model', 'year', 'title', 'description')
        }),
        ('Specifications', {
            'fields': ('mileage', 'transmission', 'fuel_type', 'engine_capacity', 'color', 'body_type', 'doors', 'seats', 'features')
        }),
        ('Pricing & Condition', {
            'fields': ('price', 'condition')
        }),
        ('Location', {
            'fields': ('city', 'state_province', 'country')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'sold_at')
        }),
    )


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ['car', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary', 'uploaded_at']
    search_fields = ['car__make', 'car__model']
    readonly_fields = ['id', 'uploaded_at']


@admin.register(CarSpecification)
class CarSpecificationAdmin(admin.ModelAdmin):
    list_display = ['car', 'horsepower', 'torque', 'top_speed']
    search_fields = ['car__make', 'car__model']
    readonly_fields = ['id', 'created_at', 'updated_at']
