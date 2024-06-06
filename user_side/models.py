from django.db import models
from django.contrib.auth.models import AbstractUser
from admins.models import Product,Coupon
from django.utils import timezone


# Create your models here.


class Users(AbstractUser):
    phone = models.CharField(max_length=25,null=True,unique=True)
    is_blocked = models.BooleanField(default=False)


class Wallet(models.Model):
    user = models.ForeignKey(Users,on_delete=models.CASCADE)
    balance = models.BigIntegerField(default=0)

#--------------------------- Cart ----------------------------


class Cart(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    is_coupon_applied = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s cart"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    total = models.DecimalField(max_digits=10, decimal_places=2,default=True)
    
    def save(self, *args, **kwargs):
        self.total = self.product.price * self.quantity
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in cart for {self.cart.user.username}"
    
class Wishlist(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'

    def __str__(self):
        return f'{self.user.username} - {self.product.title}'
    
#------------------------------- Adrress ----------------------------

class Address(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='addresses')
    name = models.CharField(max_length=25,null=True,unique=True)
    phone = models.BigIntegerField(null=True)
    address_line = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.user.username} X {self.name}"


#-------------------------------------  Order ------------------------------

class Order(models.Model):
    STATUS_CHOICES = [
        ('order_placed', 'Order Placed'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
        ('return_requested', 'Return Requested'),
        ('return_accepted', 'Return Accepted'),
        ('return_rejected', 'Return Rejected'),
        ('returned', 'Returned'),
    ]
    # REASON_CHOICES=[
    #     ('damaged_product', 'Damaged Product'),
    #     ('poor_quality', 'Poor Quality'),
    #     ('different_product', 'Different Product'),
    #     ('something_else', 'Something Else')
    # ]
    
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.DO_NOTHING, default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    coupon_code = models.CharField(blank=True,max_length=20)
    order_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=25)
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='order_placed')
    # reason = models.CharField(max_length=20,choices=REASON_CHOICES,blank=True)

    def __str__(self):
        formatted_date = self.order_date.strftime("%Y-%m-%d %H:%M:%S")
        return f"Order #{self.id}__By_{self.user.username}_on__{formatted_date}"

    
class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.BigIntegerField()
    quantity = models.IntegerField()
    
    def __str__(self):
         return f"Order #{self.order.id} for {self.product.title} by {self.order.user.username}"
    
class OrderAddress(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    name = models.CharField(max_length=25,null=True)
    phone = models.BigIntegerField(null=True)
    address_line = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)

    def __str__(self) -> str:
         return f"Order #{self.order.id}__{self.order.user.username} "



class CouponUsage(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'coupon')

