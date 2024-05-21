from django.contrib import admin
from admins.models import Category,Product,Brand,Coupon

# Register your models here.

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Brand)
admin.site.register(Coupon)
# admin.site.register(CouponUsage)