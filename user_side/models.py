from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class Users(AbstractUser):
    phone = models.CharField(max_length=25,null=True,unique=True)
    is_blocked = models.BooleanField(default=False)
    