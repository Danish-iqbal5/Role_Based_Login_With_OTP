from django.urls import path
from . import views
from .views import AdminPanel , IsManager  
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)



urlpatterns = [
    path('AdminPanel/',AdminPanel.as_view(), name='AdminPanel'),
    path('register/', views.register, name='register'),
    path('protected/', views.protected, name='protected'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('change-password/', views.change_password, name='change_password'),
    path('IsManager/', views.IsManager, name='IsManager'),
    path('create-employee/', views.create_employee, name='create_employee'),
]
