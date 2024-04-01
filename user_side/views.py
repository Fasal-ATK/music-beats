
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from user_side.models import Users
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


# Create your views here.
@login_required(login_url='ulogin')

def UserHome(request):
    return render(request,'index.html')


def Signup(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        uname = request.POST.get('uname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass')
        pass2 = request.POST.get('re_pass')
        # if len(pass1)<8:
        #     messages.error(request,"password need to be 8 or more charecters")
        if len(pass1) > 25:
            messages.error(request,"password is too big")
        elif pass1 != pass2:
            messages.error(request,"password does  not match")
        elif not uname.isalnum():
            messages.error(request,"user name is not allowed")
        else:
            new_user = Users.objects.create_user(username=uname,email=email,password=pass1,phone=phone)
            new_user.save()
            return redirect('ulogin')
    return render(request,'signup.html')
@never_cache
def Login(request):
    if request.user.is_authenticated and not request.user.is_superuser:
        return redirect('home')
    if request.method == 'POST':
        uname = request.POST.get('username')
        pswrd = request.POST.get('password')

        user = authenticate(request,username = uname, password = pswrd)
        if user is not None :
            login(request,user)
            if request.user.is_staff:
                return redirect('adminhome/')
            else:
                return redirect('home')
        else:
            messages.error(request,"username or password incorrect")
    return render(request,'login.html')

def Logout(request):
    logout(request)
    return redirect('ulogin')
