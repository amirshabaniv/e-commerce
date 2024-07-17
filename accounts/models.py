from django.db import models
from django.contrib.auth.models import (AbstractBaseUser,
                                        PermissionsMixin)
from django.core.validators import RegexValidator
from rest_framework_simplejwt.tokens import RefreshToken

from .managers import UserManager


phone_regex = RegexValidator(
    regex=r"^09\d{9}$", message="Phone number must be 11 digits only."
)


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        unique=True, max_length=11, null=False, blank=False, validators=[phone_regex]
    )
    full_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    user_registered_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "phone_number"
    REQUIRED_FIELDS = ["full_name"]

    objects = UserManager()

    def tokens(self):    
        refresh = RefreshToken.for_user(self)
        return {
            "refresh":str(refresh),
            "access":str(refresh.access_token)
        }

    def __str__(self):
        return f'{self.phone_number} - {self.full_name}'
    

