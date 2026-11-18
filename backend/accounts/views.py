from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from .serializers import RegisterSerializer, UserSerializer

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # ИСПОЛЬЗУЕМ RegisterSerializer (в котором прописаны validate_email и validate_password)
        serializer = RegisterSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            "token": token.key,
            "user": UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        user = authenticate(username=username, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------- Сброс пароля ----------

class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset/  {"email": "..."}

    Отправляет на email ссылку для сброса пароля.
    Ответ всегда одинаковый, даже если такого email нет, —
    чтобы по ответу нельзя было узнать, какие email зарегистрированы.
    В режиме разработки письмо печатается в терминал runserver (EMAIL_BACKEND = console).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response({"email": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)

        for user in User.objects.filter(email__iexact=email, is_active=True):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            send_mail(
                subject="Mini LMS: password reset",
                message=(
                    f"Hello, {user.username}!\n\n"
                    f"To set a new password, open this link:\n{link}\n\n"
                    "If you did not request a password reset, just ignore this email."
                ),
                from_email=None,  # DEFAULT_FROM_EMAIL
                recipient_list=[user.email],
            )

        return Response({"detail": "If an account with this email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    """POST /api/auth/password-reset/confirm/  {"uid": "...", "token": "...", "password": "..."}

    Проверяет ссылку из письма и ставит новый пароль.
    Ссылка одноразовая: после смены пароля токен перестаёт действовать.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid") or ""
        token = request.data.get("token") or ""
        password = request.data.get("password") or ""

        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({"token": ["Invalid or expired link."]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password, user)  # правила из AUTH_PASSWORD_VALIDATORS
        except DjangoValidationError as e:
            return Response({"password": list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        Token.objects.filter(user=user).delete()  # выйти со всех устройств со старым паролем
        return Response({"detail": "Password has been reset."})

