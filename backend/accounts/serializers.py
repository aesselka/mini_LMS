from rest_framework import serializers
from django.contrib.auth import get_user_model
import re

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=validated_data.get('role', 'student')
        )
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role']
        
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    # проверка формата и домена
    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email обязателен для заполнения.")
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            raise serializers.ValidationError("Введите корректный адрес электронной почты.")
        return value.lower()

    # мин 8 символов
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Пароль должен содержать не менее 8 символов.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)