from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import timedelta
import random
from decimal import Decimal

from cars.models import Car, CarImage, CarSpecification
from parts.models import PartCategory, CarPart, PartImage, PartCompatibility, CompanyStore
from forum.models import ForumCategory, ForumThread, ForumResponse, ResponseVote, ExpertVerification
from comments.models import Comment, CommentReply, CommentLike
from ratings.models import Rating, Review, ReviewHelpfulness
from notifications.models import Notification, NotificationPreference

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate database with sample data (excluding payment-related data)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_data()

        self.stdout.write('Creating users...')
        users = self.create_users()
        
        self.stdout.write('Creating cars...')
        cars = self.create_cars(users)
        
        self.stdout.write('Creating part categories and stores...')
        categories = self.create_part_categories()
        stores = self.create_company_stores(users)
        
        self.stdout.write('Creating car parts...')
        parts = self.create_car_parts(users, categories, stores)
        
        self.stdout.write('Creating forum data...')
        forum_categories = self.create_forum_categories()
        threads = self.create_forum_threads(users, forum_categories)
        self.create_forum_responses(users, threads)
        self.create_expert_verifications(users)
        
        self.stdout.write('Creating comments...')
        self.create_comments(users, cars, parts)
        
        self.stdout.write('Creating ratings and reviews...')
        self.create_ratings_and_reviews(users, cars)
        
        self.stdout.write('Creating notifications...')
        self.create_notifications(users)
        
        self.stdout.write(self.style.SUCCESS('✅ Database populated successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users, {len(cars)} cars, {len(parts)} parts'))

    def clear_data(self):
        """Clear existing data (except superusers)"""
        # Clear notifications
        Notification.objects.all().delete()
        NotificationPreference.objects.all().delete()
        
        # Clear ratings and reviews
        ReviewHelpfulness.objects.all().delete()
        Review.objects.all().delete()
        Rating.objects.all().delete()
        
        # Clear comments
        CommentLike.objects.all().delete()
        CommentReply.objects.all().delete()
        Comment.objects.all().delete()
        
        # Clear forum
        ResponseVote.objects.all().delete()
        ForumResponse.objects.all().delete()
        ForumThread.objects.all().delete()
        ForumCategory.objects.all().delete()
        ExpertVerification.objects.all().delete()
        
        # Clear parts
        PartCompatibility.objects.all().delete()
        PartImage.objects.all().delete()
        CarPart.objects.all().delete()
        CompanyStore.objects.all().delete()
        PartCategory.objects.all().delete()
        
        # Clear cars
        CarSpecification.objects.all().delete()
        CarImage.objects.all().delete()
        Car.objects.all().delete()
        
        # Keep admin users, delete others
        User.objects.exclude(is_superuser=True).delete()
        
        self.stdout.write(self.style.WARNING('✓ Data cleared'))

    def create_users(self):
        """Create sample users"""
        users = []
        
        # Individual buyers
        for i in range(1, 11):
            user, created = User.objects.get_or_create(
                email=f'buyer{i}@example.com',
                defaults={
                    'first_name': f'Buyer{i}',
                    'last_name': 'User',
                    'user_type': 'individual',
                    'phone_number': f'+88017000000{i:02d}',
                    'city': 'Dhaka',
                    'country': 'Bangladesh',
                    'email_verified': True,
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        # Sellers
        for i in range(1, 6):
            user, created = User.objects.get_or_create(
                email=f'seller{i}@example.com',
                defaults={
                    'first_name': f'Seller{i}',
                    'last_name': 'Auto',
                    'user_type': 'individual',
                    'phone_number': f'+88017100000{i:02d}',
                    'city': 'Dhaka',
                    'country': 'Bangladesh',
                    'email_verified': True,
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        # Companies
        for i in range(1, 4):
            user, created = User.objects.get_or_create(
                email=f'company{i}@example.com',
                defaults={
                    'first_name': 'Company',
                    'last_name': f'Parts{i}',
                    'user_type': 'company',
                    'company_name': f'AutoParts Company {i}',
                    'company_registration_number': f'REG{i:04d}',
                    'phone_number': f'+88017200000{i:02d}',
                    'city': 'Dhaka',
                    'country': 'Bangladesh',
                    'email_verified': True,
                    'verification_status': 'verified',
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            users.append(user)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(users)} users'))
        return users

    def create_cars(self, users):
        """Create sample cars"""
        cars = []
        makes_models = [
            ('Toyota', ['Corolla', 'Camry', 'Prius', 'Land Cruiser']),
            ('Honda', ['Civic', 'Accord', 'CR-V', 'Fit']),
            ('Nissan', ['Altima', 'Sentra', 'X-Trail', 'Pathfinder']),
            ('Mazda', ['Mazda3', 'Mazda6', 'CX-5', 'CX-9']),
            ('Mitsubishi', ['Lancer', 'Outlander', 'Pajero', 'ASX']),
        ]
        
        conditions = ['excellent', 'good', 'fair']
        transmissions = ['automatic', 'manual']
        fuel_types = ['petrol', 'diesel', 'hybrid']
        colors = ['Black', 'White', 'Silver', 'Red', 'Blue', 'Gray']
        body_types = ['sedan', 'suv', 'hatchback', 'coupe']
        
        sellers = [u for u in users if 'seller' in u.email]
        
        for i in range(30):
            make, models = random.choice(makes_models)
            model = random.choice(models)
            year = random.randint(2015, 2024)
            
            car = Car.objects.create(
                seller=random.choice(sellers),
                make=make,
                model=model,
                year=year,
                mileage=random.randint(10000, 150000),
                transmission=random.choice(transmissions),
                fuel_type=random.choice(fuel_types),
                engine_capacity=Decimal(str(round(random.uniform(1.2, 3.5), 1))),
                condition=random.choice(conditions),
                price=Decimal(str(random.randint(500000, 5000000))),
                title=f'{year} {make} {model}',
                description=f'Well maintained {year} {make} {model} in {random.choice(conditions)} condition. Perfect for daily commute.',
                city=random.choice(['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi', 'Khulna']),
                state_province='Dhaka Division',
                country='Bangladesh',
                status='active',
                color=random.choice(colors),
                body_type=random.choice(body_types),
                doors=random.choice([2, 4]),
                seats=random.choice([4, 5, 7]),
                is_featured=random.choice([True, False]),
                features=['AC', 'Power Steering', 'ABS', 'Airbags', 'Sunroof'][:random.randint(2, 5)]
            )
            cars.append(car)
            
            # Add specifications
            CarSpecification.objects.create(
                car=car,
                horsepower=random.randint(100, 300),
                torque=random.randint(150, 400),
                acceleration_0_100=Decimal(str(round(random.uniform(6.0, 15.0), 1))),
                top_speed=random.randint(160, 240),
                fuel_consumption_city=Decimal(str(round(random.uniform(8, 15), 1))),
                fuel_consumption_highway=Decimal(str(round(random.uniform(6, 12), 1))),
                length=Decimal(str(round(random.uniform(4.2, 5.2), 2))),
                width=Decimal(str(round(random.uniform(1.7, 2.0), 2))),
                height=Decimal(str(round(random.uniform(1.4, 1.8), 2))),
                weight=random.randint(1200, 2500)
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(cars)} cars'))
        return cars

    def create_part_categories(self):
        """Create part categories"""
        categories_data = [
            {'name': 'Engine Parts', 'description': 'Engine components and accessories'},
            {'name': 'Brake System', 'description': 'Brake pads, rotors, and components'},
            {'name': 'Suspension', 'description': 'Suspension parts and shock absorbers'},
            {'name': 'Electrical', 'description': 'Electrical components and wiring'},
            {'name': 'Body Parts', 'description': 'Exterior and interior body parts'},
            {'name': 'Filters', 'description': 'Oil, air, and fuel filters'},
            {'name': 'Lighting', 'description': 'Headlights, tail lights, and bulbs'},
            {'name': 'Cooling System', 'description': 'Radiators and cooling components'},
        ]
        
        categories = []
        for data in categories_data:
            category, created = PartCategory.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories)} part categories'))
        return categories

    def create_company_stores(self, users):
        """Create company stores"""
        stores = []
        companies = [u for u in users if u.user_type == 'company']
        
        for company in companies:
            store, created = CompanyStore.objects.get_or_create(
                company=company,
                defaults={
                    'store_name': f'{company.company_name} Store',
                    'store_description': f'Official store of {company.company_name}. We provide quality auto parts.',
                    'store_email': company.email,
                    'store_phone': company.phone_number,
                    'store_address': '123 Auto Street',
                    'store_city': 'Dhaka',
                    'store_state': 'Dhaka Division',
                    'store_country': 'Bangladesh',
                    'is_verified': True,
                    'is_active': True
                }
            )
            stores.append(store)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(stores)} company stores'))
        return stores

    def create_car_parts(self, users, categories, stores):
        """Create car parts"""
        parts = []
        conditions = ['new', 'refurbished', 'used']
        brands = ['OEM', 'Aftermarket', 'Genuine', 'Premium', 'Budget']
        
        sellers = [u for u in users if u.user_type == 'company']
        
        part_names = {
            'Engine Parts': ['Oil Filter', 'Air Filter', 'Spark Plugs', 'Timing Belt', 'Fuel Pump'],
            'Brake System': ['Brake Pad Set', 'Brake Rotor', 'Brake Caliper', 'Brake Fluid'],
            'Suspension': ['Shock Absorber', 'Strut Assembly', 'Control Arm', 'Ball Joint'],
            'Electrical': ['Alternator', 'Starter Motor', 'Battery', 'Ignition Coil'],
            'Body Parts': ['Headlight Assembly', 'Tail Light', 'Side Mirror', 'Bumper'],
            'Filters': ['Oil Filter', 'Air Filter', 'Cabin Filter', 'Fuel Filter'],
            'Lighting': ['Headlight Bulb', 'LED Light', 'Fog Light', 'Turn Signal'],
            'Cooling System': ['Radiator', 'Water Pump', 'Thermostat', 'Coolant Hose']
        }
        
        for i in range(50):
            category = random.choice(categories)
            available_parts = part_names.get(category.name, ['Generic Part'])
            
            part = CarPart.objects.create(
                seller=random.choice(sellers),
                category=category,
                name=random.choice(available_parts),
                description=f'High quality {random.choice(available_parts)} for various car models. Tested and verified.',
                part_number=f'PN{random.randint(10000, 99999)}',
                condition=random.choice(conditions),
                brand=random.choice(brands),
                price=Decimal(str(random.randint(500, 50000))),
                quantity_in_stock=random.randint(5, 100),
                status='active',
                warranty_months=random.choice([3, 6, 12, 24]),
                is_featured=random.choice([True, False])
            )
            parts.append(part)
            
            # Add compatibility
            makes = ['Toyota', 'Honda', 'Nissan', 'Mazda', 'Mitsubishi']
            for _ in range(random.randint(1, 3)):
                make = random.choice(makes)
                models = {'Toyota': ['Corolla', 'Camry'], 'Honda': ['Civic', 'Accord'],
                         'Nissan': ['Altima'], 'Mazda': ['Mazda3'], 'Mitsubishi': ['Lancer']}
                
                PartCompatibility.objects.get_or_create(
                    part=part,
                    car_make=make,
                    car_model=random.choice(models.get(make, ['Generic'])),
                    car_year_from=random.randint(2010, 2018),
                    car_year_to=random.randint(2019, 2024)
                )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(parts)} car parts'))
        return parts

    def create_forum_categories(self):
        """Create forum categories"""
        categories_data = [
            {'name': 'General Discussion', 'description': 'General car discussions and topics'},
            {'name': 'Engine & Performance', 'description': 'Engine tuning and performance topics'},
            {'name': 'Maintenance & Repair', 'description': 'Maintenance tips and repair help'},
            {'name': 'Buying Guide', 'description': 'Help with buying decisions and advice'},
            {'name': 'Car Reviews', 'description': 'Share and read car reviews'},
        ]
        
        categories = []
        for data in categories_data:
            category, created = ForumCategory.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description'], 'is_active': True}
            )
            categories.append(category)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(categories)} forum categories'))
        return categories

    def create_forum_threads(self, users, categories):
        """Create forum threads"""
        threads = []
        titles = [
            'Best oil for Honda Civic 2020?',
            'Toyota Corolla vs Honda Civic - Which is better?',
            'How to fix engine overheating issue?',
            'Best time to change brake pads?',
            'Recommendations for first car buyer',
            'Hybrid vs Petrol - Long term costs comparison',
            'Weird noise from suspension when turning',
            'Car insurance recommendations in Dhaka',
            'Best garage in Dhaka for routine maintenance?',
            'Fuel efficiency tips for city driving',
            'AC not cooling properly - what to check?',
            'Should I buy a used car or new?',
            'Best cars under 3 million taka',
            'How often should I service my car?',
            'Transmission problems - automatic vs manual'
        ]
        
        for i in range(20):
            thread = ForumThread.objects.create(
                author=random.choice(users),
                category=random.choice(categories),
                title=random.choice(titles),
                description=f'I need help with {random.choice(titles).lower()}. Any suggestions would be appreciated. Thanks!',
                car_make=random.choice(['Toyota', 'Honda', 'Nissan', 'Mazda', 'Any', None]),
                car_model=random.choice(['Corolla', 'Civic', 'Altima', 'Mazda3', 'Any', None]),
                car_year=random.choice([2015, 2018, 2020, 2022, None]),
                status='open',
                is_pinned=random.choice([True, False]) if i < 3 else False,
                views_count=random.randint(10, 500)
            )
            threads.append(thread)
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(threads)} forum threads'))
        return threads

    def create_forum_responses(self, users, threads):
        """Create forum responses"""
        response_count = 0
        for thread in threads:
            num_responses = random.randint(1, 5)
            for _ in range(num_responses):
                response = ForumResponse.objects.create(
                    thread=thread,
                    author=random.choice(users),
                    content=f'Based on my experience, I would recommend checking the manufacturer guidelines. This is a helpful response to your question.',
                    is_expert_response=random.choice([True, False]),
                    helpful_count=random.randint(0, 20)
                )
                response_count += 1
                
                # Add some votes
                num_votes = random.randint(0, 3)
                voters = random.sample(users, min(num_votes, len(users)))
                for voter in voters:
                    ResponseVote.objects.get_or_create(
                        response=response,
                        user=voter,
                        defaults={'vote_type': random.choice(['helpful', 'unhelpful'])}
                    )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {response_count} forum responses'))

    def create_expert_verifications(self, users):
        """Create expert verifications"""
        expertise_options = [
            ['Engine Repair', 'Transmission'],
            ['Electrical Systems', 'Diagnostics'],
            ['Body Work', 'Painting'],
            ['Brake Systems', 'Suspension'],
            ['AC Systems', 'Cooling']
        ]
        
        experts = random.sample(users, min(5, len(users)))
        for expert in experts:
            ExpertVerification.objects.get_or_create(
                user=expert,
                defaults={
                    'expertise_areas': random.choice(expertise_options),
                    'years_of_experience': random.randint(5, 20),
                    'bio': f'Professional mechanic with {random.randint(5, 20)} years of experience in automotive repair.',
                    'status': 'approved',
                    'verified_at': timezone.now()
                }
            )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {len(experts)} expert verifications'))

    def create_comments(self, users, cars, parts):
        """Create comments on cars and parts"""
        comment_count = 0
        car_content_type = ContentType.objects.get_for_model(Car)
        part_content_type = ContentType.objects.get_for_model(CarPart)
        
        # Comments on cars
        sample_cars = random.sample(cars, min(10, len(cars)))
        for car in sample_cars:
            num_comments = random.randint(1, 3)
            for _ in range(num_comments):
                comment = Comment.objects.create(
                    author=random.choice(users),
                    content_type=car_content_type,
                    object_id=car.id,
                    text=random.choice([
                        'Great car! Interested in buying.',
                        'Is this still available?',
                        'What is the accident history?',
                        'Can you provide more photos?'
                    ]),
                    likes_count=random.randint(0, 10),
                    is_approved=True
                )
                comment_count += 1
                
                # Add reply
                if random.choice([True, False]):
                    CommentReply.objects.create(
                        comment=comment,
                        author=car.seller,
                        text='Thank you for your interest! Feel free to contact me for more details.',
                        likes_count=random.randint(0, 5),
                        is_approved=True
                    )
        
        # Comments on parts
        sample_parts = random.sample(parts, min(10, len(parts)))
        for part in sample_parts:
            num_comments = random.randint(1, 2)
            for _ in range(num_comments):
                Comment.objects.create(
                    author=random.choice(users),
                    content_type=part_content_type,
                    object_id=part.id,
                    text=random.choice([
                        'Does this fit 2018 model?',
                        'Is warranty included?',
                        'How long for delivery?',
                        'Original or aftermarket?'
                    ]),
                    likes_count=random.randint(0, 5),
                    is_approved=True
                )
                comment_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {comment_count} comments'))

    def create_ratings_and_reviews(self, users, cars):
        """Create ratings and reviews"""
        sample_cars = random.sample(cars, min(10, len(cars)))
        buyers = [u for u in users if 'buyer' in u.email]
        review_count = 0
        
        # Track which reviewer has reviewed which seller to avoid duplicates
        reviewed_pairs = set()
        
        for car in sample_cars:
            # Get or create rating for seller
            rating, created = Rating.objects.get_or_create(
                seller=car.seller,
                defaults={
                    'average_rating': Decimal('0'),
                    'total_reviews': 0
                }
            )
            
            # Create reviews - ensure unique reviewer-seller pairs
            num_reviews = random.randint(1, 3)
            available_buyers = [b for b in buyers if (b.id, car.seller.id) not in reviewed_pairs]
            
            for _ in range(min(num_reviews, len(available_buyers))):
                if not available_buyers:
                    break
                    
                reviewer = random.choice(available_buyers)
                available_buyers.remove(reviewer)
                reviewed_pairs.add((reviewer.id, car.seller.id))
                
                review_rating = random.randint(4, 5)
                Review.objects.create(
                    reviewer=reviewer,
                    seller=car.seller,
                    title=random.choice(['Great seller!', 'Smooth transaction', 'Highly recommended', 'Good experience']),
                    text='Excellent experience buying from this seller. Quick response and honest dealing. Would recommend!',
                    rating=review_rating,
                    communication_rating=review_rating,
                    item_accuracy_rating=review_rating,
                    shipping_rating=review_rating,
                    is_verified_purchase=True,
                    helpful_count=random.randint(0, 10),
                    is_approved=True
                )
                review_count += 1
            
            # Update rating
            rating.update_from_reviews()
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {review_count} reviews'))

    def create_notifications(self, users):
        """Create notifications"""
        notification_types = [
            'new_message', 'listing_update', 'expert_response',
            'forum_reply', 'system_announcement', 'review_received'
        ]
        
        notif_count = 0
        for user in users[:10]:  # Create for first 10 users
            # Create notification preferences with default values
            NotificationPreference.objects.get_or_create(
                user=user,
                defaults={
                    'email_new_message': True,
                    'email_listing_update': True,
                    'app_new_message': True,
                    'app_listing_update': True,
                    'email_frequency': 'instant'
                }
            )
            
            # Create sample notifications
            for _ in range(random.randint(2, 5)):
                Notification.objects.create(
                    user=user,
                    notification_type=random.choice(notification_types),
                    title='New notification',
                    message='You have a new notification in your account.',
                    is_read=random.choice([True, False])
                )
                notif_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Created {notif_count} notifications'))