from users.models import CustomUser
from rest_framework import viewsets
from users.api.serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer