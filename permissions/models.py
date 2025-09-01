from django.db import models

from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class EmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6) 
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() > self.expires_at

class Profile(models.Model):
    ROLE_CHOICES = (
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )
    
    EMPLOYEE_ROLE_CHOICES = (
        ('cashier', 'Cashier'),
        ('inventory', 'Inventory Manager'),
        ('sales', 'Salesperson'),
        ('support', 'Support Staff'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_users', null=True, blank=True)
    
    employee_role = models.CharField(max_length=20, choices=EMPLOYEE_ROLE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role} - {self.employee_role or 'N/A'}"