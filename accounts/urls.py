from django.urls import path
from . import views


app_name = 'accounts'
urlpatterns = [
    path('register/', views.RegisterAPIView.as_view(), name='user_register'),
    path('verify/', views.VerifyAPIView.as_view(), name='verify_otp'),
    path('login/', views.LoginAPIView.as_view(), name='user_login'),
    path('forgot/password/', views.ForgotPasswordAPIView.as_view(), name='forgot_password'),
    path('reset/password/', views.SetNewPasswordAPIView.as_view(), name='reset_password'),
    path('logout/', views.LogoutAPIView.as_view(), name='user_logout'),
]