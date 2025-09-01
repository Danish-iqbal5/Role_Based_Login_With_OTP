from django.shortcuts import render
from rest_framework.views import APIView , Response
from django.contrib.auth.models import  User 
from rest_framework.permissions import IsAdminUser ,IsAuthenticated
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
from datetime import timedelta
from .models import EmailVerification , Profile
from .utils import generate_otp  
from django.utils import timezone# OTP generator function
from django.core.mail import send_mail 
from .permissions import IsManager

# Create your views here.
class AdminPanel(APIView):
    pass
#     permission_classes = [IsAdminUser]
#     def get(self, request):
#         return Response({"message": "Welcome to the Admin Panel!"})



@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    email = request.data.get('email')

    if not username or not email:
        return Response({"error": "Username and email are required."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({"error": "Email already registered."}, status=status.HTTP_400_BAD_REQUEST)

    # Create user inactive and without password (password will be set after OTP verification)
    user = User.objects.create(username=username, email=email, is_active=False)

    # Generate OTP and expiry time
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=15)

    # Create or update EmailVerification for this user
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            'otp': otp,
            'expires_at': expires_at,
            'is_verified': False
        }
    )

    # Send OTP email (update with your email sending config)
    send_mail(
        subject="Your OTP Code",
        message=f"Hello {username}, your OTP code is {otp}. It expires in 15 minutes.",
        from_email="no-reply@yourdomain.com",
        recipient_list=[email],
        fail_silently=False,
    )

    return Response({"msg": "User registered successfully. Please check your email for the OTP to verify your account."}, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    email = request.data.get('email')
    otp = request.data.get('otp')
    password = request.data.get('password')

    if not email or not otp or not password:
        return Response({"error": "Email, OTP, and password are required."}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
        verification = EmailVerification.objects.get(user=user)
    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except EmailVerification.DoesNotExist:
        return Response({"error": "No OTP request found for this user."}, status=status.HTTP_404_NOT_FOUND)

    if verification.is_verified:
        return Response({"error": "User already verified."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.is_expired():
        return Response({"error": "OTP expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)

    if verification.otp != otp:
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    # OTP is valid
    user.set_password(password)  # Set password now
    user.is_active = True  # Activate user
    user.save()

    verification.is_verified = True
    verification.save()

    return Response({"msg": "OTP verified, password set, user activated. You can now login."}, status=status.HTTP_200_OK)



# Protected view
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected(request):
    return Response({"msg": f"Hello {request.user.username}, you're authenticated!"})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsManager])
def create_employee(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not email or not password:
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password, is_active=True)

    # Assign employee role + link to manager
    Profile.objects.filter(user=user).update(role='employee', created_by=request.user)

    return Response({"msg": f"Employee '{username}' created successfully."}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')

    user = request.user

    if not user.check_password(old_password):
        return Response({"error": "Old password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    return Response({"msg": "Password changed successfully"}, status=status.HTTP_200_OK)

from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'profile') and request.user.profile.role == 'manager'
