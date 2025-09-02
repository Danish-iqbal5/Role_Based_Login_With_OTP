from django.contrib import admin

# Register your models here.

from .models import EmailVerification, Profile , Products

admin.site.register(EmailVerification)
admin.site.register(Profile)
admin.site.register(Products)