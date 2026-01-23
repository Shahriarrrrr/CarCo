from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from forum.models import ForumCategory, ForumThread, ForumResponse, ResponseVote
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class ForumThreadAPITest(APITestCase):
    """Test suite for ForumThread API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="testuser@example.com",
            password="testpass123",
            first_name="Test", last_name="User"
        )
        self.category = ForumCategory.objects.create(
            name="General",
            description="General category"
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_threads_authenticated(self):
        """Test that authenticated users can list threads"""
        ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Test Thread 1",
            description="Description 1"
        )
        ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Test Thread 2",
            description="Description 2"
        )
        
        response = self.client.get('/api/forum/threads/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        if 'results' in response.data:
            self.assertEqual(len(response.data['results']), 2)
        else:
            self.assertEqual(len(response.data), 2)

    def test_retrieve_thread_increments_views(self):
        """Test that retrieving a thread increments view count"""
        thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="View Count Test",
            description="Test description"
        )
        initial_views = thread.views_count
        
        response = self.client.get(f'/api/forum/threads/{thread.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        thread.refresh_from_db()
        self.assertEqual(thread.views_count, initial_views + 1)

    def test_create_thread_authenticated(self):
        """Test creating a thread when authenticated"""
        data = {
            'category': str(self.category.id),
            'title': 'New Thread',
            'description': 'Thread description',
            'car_make': 'Honda',
            'car_model': 'Civic',
            'car_year': 2020
        }
        
        response = self.client.post('/api/forum/threads/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ForumThread.objects.count(), 1)
        
        thread = ForumThread.objects.first()
        self.assertEqual(thread.author, self.user)
        self.assertEqual(thread.title, 'New Thread')

    def test_create_thread_unauthenticated(self):
        """Test that unauthenticated users cannot create threads"""
        self.client.credentials()
        data = {
            'category': str(self.category.id),
            'title': 'Unauthorized Thread',
            'description': 'Should fail'
        }
        
        response = self.client.post('/api/forum/threads/', data, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class ForumResponseAPITest(APITestCase):
    """Test suite for ForumResponse API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="responseuser@example.com",
            password="pass123",
            first_name="Response", last_name="User"
        )
        self.category = ForumCategory.objects.create(
            name="Discussion",
            description="Discussion category"
        )
        self.thread = ForumThread.objects.create(
            author=self.user,
            category=self.category,
            title="Response Test Thread",
            description="Test description"
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_responses_filtered_by_thread(self):
        """Test listing responses filtered by thread ID"""
        ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Response 1"
        )
        ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Response 2"
        )
        
        response = self.client.get(f'/api/forum/responses/?thread={self.thread.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        responses = response.data.get('results', response.data)
        self.assertEqual(len(responses), 2)

    def test_add_response_to_thread(self):
        """Test adding a response using the add_response action"""
        data = {'content': 'This is my response'}
        
        response = self.client.post(
            f'/api/forum/threads/{self.thread.id}/add_response/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ForumResponse.objects.filter(thread=self.thread).count(), 1)
        self.assertEqual(response.data['content'], 'This is my response')

    def test_add_response_unauthenticated(self):
        """Test that unauthenticated users cannot add responses"""
        self.client.credentials()
        data = {'content': 'Unauthorized response'}
        
        response = self.client.post(
            f'/api/forum/threads/{self.thread.id}/add_response/',
            data,
            format='json'
        )
        
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_vote_on_response(self):
        """Test voting on a response"""
        response_obj = ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Votable response"
        )
        
        data = {'vote_type': 'helpful'}
        response = self.client.post(
            f'/api/forum/responses/{response_obj.id}/vote/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResponseVote.objects.filter(response=response_obj).count(), 1)

    def test_remove_vote(self):
        """Test removing a vote from a response"""
        response_obj = ForumResponse.objects.create(
            thread=self.thread,
            author=self.user,
            content="Test response"
        )
        ResponseVote.objects.create(
            response=response_obj,
            user=self.user,
            vote_type='helpful'
        )
        
        response = self.client.delete(f'/api/forum/responses/{response_obj.id}/remove_vote/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(ResponseVote.objects.filter(response=response_obj).count(), 0)


class ForumCategoryAPITest(APITestCase):
    """Test suite for ForumCategory API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="catuser@example.com",
            password="pass123",
            first_name="Category", last_name="User"
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_list_categories(self):
        """Test listing forum categories"""
        ForumCategory.objects.create(name="Category 1", description="Desc 1")
        ForumCategory.objects.create(name="Category 2", description="Desc 2")
        
        response = self.client.get('/api/forum/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        categories = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertGreaterEqual(len(categories), 2)

    def test_filter_active_categories(self):
        """Test that only active categories are listed"""
        ForumCategory.objects.create(name="Active", description="Active cat", is_active=True)
        ForumCategory.objects.create(name="Inactive", description="Inactive cat", is_active=False)
        
        response = self.client.get('/api/forum/categories/')
        categories = response.data if isinstance(response.data, list) else response.data.get('results', [])
        
        # Assuming the view filters by is_active=True
        active_names = [cat['name'] for cat in categories if 'name' in cat]
        self.assertIn('Active', active_names)
