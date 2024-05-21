from django.contrib import admin
from user_side.models import Users,Cart,CartItem,Address,Order,OrderItem,OrderAddress,CouponUsage,Wishlist

# Register your models here.

admin.site.register(Users)
admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(OrderAddress)
admin.site.register(CouponUsage)
admin.site.register(Wishlist)
