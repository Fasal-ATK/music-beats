from . import views
from django.urls import path


urlpatterns = [
    path('',views.UserHome,name='home'),
    path('ulogin/',views.Login,name='ulogin'),
    path('signup/',views.Signup, name='signup'),
    path('ulogout/',views.Logout,name='ulogout'),
]
