from . import views
from django.urls import path


urlpatterns = [
    path('',views.UserHome,name='home'),

    path('signup/',views.Signup, name='signup'),
    path('verify_otp/',views.Verify_OTP,name='verify_otp'),

    path('ulogin/',views.Login,name='ulogin'),
    path('ulogout/',views.Logout,name='ulogout'),

    path('shop/',views.Shop,name='shop'),
    path('single/<int:id>/',views.Single_Product,name='single'),

    path('cart/', views.Cart_Page, name='cart'),
    path('add-cart/<int:product_id>/', views.Add_Cart, name='add-cart'),
    path('remove-cart/<int:cartitem_id>/', views.Remove_Cart, name='remove-cart'),
    path('update-cart/<int:cartitem_id>/', views.Update_Cart, name='update-cart'),

    path('profile/',views.User_Profile,name='profile'),
    path('add-address/',views.Add_Address,name='add-address'),     
    path('edit-address/<int:address_id>/',views.Edit_Address,name='edit-address'),
    path('delete-address/<int:address_id>',views.Delete_Address,name='delete-address'),
    path('change-password/',views.Change_Password,name='change-password'),

    path('checkout/',views.Product_Checkout,name='checkout'),
    path('place-order/',views.Place_Order,name='place-order'),
    
    path('order-page/',views.Order_Page,name='order-page'),
    path('order-details/<int:order_id>/',views.Order_Details,name='order-details'),
    path('order-tracking/',views.Order_Tracking,name='order-tracking'),
]


# adil = 12345678

# nivin = 12121212