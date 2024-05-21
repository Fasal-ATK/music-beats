from django.utils import timezone
from django.db import models
from django.core.exceptions import ValidationError


# create your models here


class Category(models.Model):
    name = models.CharField(max_length = 50)
    description = models.TextField()
    is_listed = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    title = models.CharField(max_length = 100)
    price =  models.FloatField()
    category = models.ForeignKey(Category, on_delete = models.CASCADE)
    description = models.TextField(null=True)
    image = models.ImageField(upload_to='product/', blank=True)
    stock = models.BigIntegerField()
    is_listed = models.BooleanField(default=True)

    def is_in_stock(self):
        return self.stock > 0

    def __str__(self) :
        return self.title 


#--------------------------- Brand ----------------------------


class Brand(models.Model):
    name = models.CharField(max_length = 100)
    logo = models.ImageField(upload_to='brand_logo/', null=True, blank=True)
    is_listed = models.BooleanField(default = True)

    def __str__(self) -> str:
        return self.name


#--------------------------- Coupen ----------------------------


class Coupon(models.Model):
    coupon_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expire_date = models.DateTimeField()
    discount_price = models.IntegerField(default=100)
    minimum_amount = models.IntegerField(default=2000)
    is_expired = models.BooleanField(default=False)
    active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.coupon_code} (created at {self.created_at})'

    def clean(self):
        if self.expire_date <= self.created_at:
            raise ValidationError("Expire date must be after the created date.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Call clean method to validate before saving
        self.is_expired = self.check_if_expired()
        super().save(*args, **kwargs)

    def check_if_expired(self):
        return timezone.now() > self.expire_date

    def apply_discount(self, total_amount):
        if self.is_expired:
            raise ValidationError("This coupon is expired.")
        if total_amount < self.minimum_amount:
            raise ValidationError(f"The total amount must be at least {self.minimum_amount} to use this coupon.")
        return total_amount - self.discount_price

