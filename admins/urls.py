from . import views
from django.urls import path


urlpatterns = [
    path('usermanager/',views.AdminHome,name='usermanager'),
    path('adminlogin/',views.AdminLogin,name='adminlogin'),
    path('dash/',views.Dashboard,name='dash'),

    path('block/<int:id>',views.BlockUser,name='block'),
    
    path('signout/',views.AdminLogout,name='signout'),
    path('product/', views.ProductManager, name='product'),
    path('category/',views.CategoryManager,name='category'),
]