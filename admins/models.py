from django.db import models
from django.contrib.postgres.fields import ArrayField


# Product Models

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
    image = ArrayField(models.ImageField(upload_to='media/'), blank=True)
    stock = models.BigIntegerField()
    is_listed = models.BooleanField(default=True)

    def __str__(self) :
        return self.title 


