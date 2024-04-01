from . import views
from django.urls import path


urlpatterns = [
    path('adminhome/',views.AdminHome,name='adminhome'),
    path('adminlogin/',views.AdminLogin,name='adminlogin'),

]
