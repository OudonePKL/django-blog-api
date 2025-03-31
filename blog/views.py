from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from .models import Article, Tag
from .serializers import ArticleSerializer, TagSerializer, RegisterSerializer, RequestOTPSerializer
from django.contrib.auth import get_user_model
from django_filters import FilterSet, DateFromToRangeFilter, CharFilter
import random
import string
from django.conf import settings
from django.core.mail import send_mail


User = get_user_model()

class RequestOTPView(APIView):
    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.save()
        
        return Response(
            {'message': f'OTP sent to {email}'}, 
            status=status.HTTP_200_OK
        )

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response(
            {
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                },
                'message': 'Registration successful'
            },
            status=status.HTTP_201_CREATED
        )

class ArticleFilter(FilterSet):
    published_date = DateFromToRangeFilter()
    tags = CharFilter(method='filter_by_tag')
    
    class Meta:
        model = Article
        fields = {
            'author': ['exact'], 
            'tags': ['exact'], 
            'title':['icontains'], 
            'content':['icontains']
        }

    def filter_by_tag(self, queryset, name, value):
        try:
            # Try to filter by ID if value is numeric
            tag_id = int(value)
            return queryset.filter(tags__id=tag_id)
        except ValueError:
            # Fall back to name filtering
            return queryset.filter(tags__name__iexact=value)

class ArticleListCreateView(generics.ListCreateAPIView):
    queryset = Article.objects.filter(is_published=True)
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ArticleFilter
    search_fields = ['title', 'content']
    ordering_fields = ['published_date', 'updated_date']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

class ArticleRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_update(self, serializer):
        serializer.save(author=self.request.user)

class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

