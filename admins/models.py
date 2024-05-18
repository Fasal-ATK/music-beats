from django.db import models


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

    def __str__(self) :
        return self.title 


#--------------------------- Brand ----------------------------


class Brand(models.Model):
    name = models.CharField(max_length = 100)
    logo = models.ImageField(upload_to='brand_logo/', null=True, blank=True)
    is_listed = models.BooleanField(default = True)

    def __str__(self) -> str:
        return self.name