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
from django.utils import timezone
from django.core.mail import send_mail 
from .permissions import IsManager

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

   
    user = User.objects.create(username=username, email=email, is_active=False)

    
    otp = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=15)

    
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            'otp': otp,
            'expires_at': expires_at,
            'is_verified': False
        }
    )


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


    user.set_password(password) 
    user.is_active = True
    user.save()

    verification.is_verified = True
    verification.save()

    return Response({"msg": "OTP verified, password set, user activated. You can now login."}, status=status.HTTP_200_OK)




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
    employee_role = request.data.get('employee_role')

    if not all([username, email, password, employee_role]):
        return Response({"error": "All fields are required."}, status=400)

    if employee_role not in dict(Profile.EMPLOYEE_ROLE_CHOICES):
        return Response({"error": "Invalid employee role."}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists."}, status=400)

    user = User.objects.create_user(username=username, email=email, password=password, is_active=True)

   
    Profile.objects.filter(user=user).update(
        role='employee',
        created_by=request.user,
        employee_role=employee_role
    )

    return Response({"msg": f"Employee '{username}' created with role '{employee_role}'."}, status=201)



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
