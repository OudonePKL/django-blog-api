from rest_framework import serializers
from .models import Article, Tag
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.core.mail import send_mail
from django.conf import settings
from django.core.cache import cache
import random
import string


User = get_user_model()

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def save(self):
        email = self.validated_data['email']
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Store OTP in cache for 5 minutes
        cache.set(f'reg_otp_{email}', otp, timeout=300)

        print("Cache 1 : ", cache)
        
        # Send OTP via email
        send_mail(
            'Your Registration OTP',
            f'Your registration code is: {otp}\nThis code expires in 5 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return email
    
class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    otp = serializers.CharField(write_only=True, required=True, max_length=6)
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password2', 'otp')

    def validate(self, attrs):
        # Check passwords match
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        # Verify OTP
        email = attrs['email']
        cached_otp = cache.get(f'reg_otp_{email}')

        print("cached_otp : ", cached_otp)
        
        if not cached_otp:
            raise serializers.ValidationError({"otp": "OTP expired or invalid"})
        
        if attrs['otp'] != cached_otp:
            raise serializers.ValidationError({"otp": "Invalid OTP"})
        
        return attrs

    def create(self, validated_data):
        # Remove OTP and password2 from validated data
        validated_data.pop('otp')
        validated_data.pop('password2')
        
        # Create and return user
        user = User.objects.create_user(
            **validated_data,
            is_active=True  # Already verified via OTP
        )
        
        # Clear used OTP
        cache.delete(f'reg_otp_{validated_data["email"]}')
        return user

class TagRelatedField(serializers.RelatedField):
    def to_internal_value(self, data):
        if isinstance(data, int):
            return Tag.objects.get(id=data)
        elif isinstance(data, str):
            tag, created = Tag.objects.get_or_create(name=data)
            return tag
        raise serializers.ValidationError("Tag must be ID or name")

    def to_representation(self, value):
        return {'id': value.id, 'name': value.name}

class ArticleSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagRelatedField(
        many=True,
        queryset=Tag.objects.all(),
        required=False
    )
    
    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'author', 'published_date', 
                 'updated_date', 'tags', 'is_published']

    