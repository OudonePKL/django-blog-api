from django.urls import path
from .views import (
    ArticleListCreateView,
    ArticleRetrieveUpdateDestroyView,
    TagListView,
    RegisterView,
    RequestOTPView
)

urlpatterns = [
    path('articles/', ArticleListCreateView.as_view(), name='article-list-create'),
    path('articles/<int:pk>/', ArticleRetrieveUpdateDestroyView.as_view(), name='article-retrieve-update-destroy'),
    path('tags/', TagListView.as_view(), name='tag-list'),
    path('request-otp/', RequestOTPView.as_view(), name='request-otp'),
    path('register/', RegisterView.as_view(), name='register'),

]