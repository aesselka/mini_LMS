from django.urls import path
from .views import (LoginView, LogoutView, PasswordResetConfirmView, PasswordResetRequestView,
                    RegisterView, UserListView, UserProfileView, AdminStatsView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('me/', UserProfileView.as_view(), name='profile'),
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('admin-stats/', AdminStatsView.as_view(), name='admin-stats'),
]