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
from .permissions import IsAdminRole
from courses.models import Course

User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # use RegisterSerializer
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
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def patch(self, request):
        allowed = {k: v for k, v in request.data.items()
                   if k in ('first_name', 'last_name', 'email')}
        serializer = UserSerializer(request.user, data=allowed, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
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

        dev_link = None
        for user in User.objects.filter(email__iexact=email, is_active=True):
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            link = f"{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}"
            dev_link = link
            text = (
                f"Hello, {user.username}!\n\n"
                f"To set a new password, open this link:\n{link}\n\n"
                "The link is valid for 1 hour.\n"
                "If you did not request a password reset, just ignore this email."
            )
            html = f"""
<div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;padding:24px;border:1px solid #e5e7eb;border-radius:16px">
  <h2 style="margin:0 0 8px;color:#4f46e5">CapyClass</h2>
  <p>Hello, <b>{user.username}</b>!</p>
  <p>We received a request to reset your password. Click the button to set a new one:</p>
  <p style="text-align:center;margin:24px 0">
    <a href="{link}" style="background:#4f46e5;color:#fff;padding:12px 24px;border-radius:10px;text-decoration:none;font-weight:bold">Reset password</a>
  </p>
  <p style="color:#6b7280;font-size:13px">The link is valid for 1 hour. If you did not request a password reset, just ignore this email.</p>
</div>"""
            try:
                send_mail(
                    subject="CapyClass: password reset",
                    message=text,
                    html_message=html,
                    from_email=None,  # DEFAULT_FROM_EMAIL
                    recipient_list=[user.email],
                )
            except Exception as exc:
                # Ошибку видно в терминале runserver (неверный пароль, Mailpit не запущен...)
                print(f"[password reset] email was not sent: {exc}")

        data = {"detail": "If an account with this email exists, a reset link has been sent."}
        # Только в режиме разработки (DEBUG=True): отдаём ссылку фронтенду,
        # чтобы проверять сброс без почты. В продакшене (DEBUG=False) её нет.
        if settings.DEBUG and dev_link:
            data["dev_reset_link"] = dev_link
        return Response(data)


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

    
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
        return Response(
            {"message": "Successfully logged out. Token deleted."},
            status=status.HTTP_200_OK
        )
        
    
class UserListView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data, status=status.HTTP_200_OK)

class AdminStatsView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        return Response({
            'students': User.objects.filter(role='student').count(),
            'teachers': User.objects.filter(role='teacher').count(),
            'admins': User.objects.filter(role='admin').count(),
            'courses': Course.objects.count(),
        }, status=status.HTTP_200_OK)
