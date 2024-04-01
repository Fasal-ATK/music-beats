from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
# Create your views here.

def AdminHome(request):
    return render(request,'adminhome.html')

def AdminLogin(request):
    if request.user.is_staff:
        if request.method == 'POST':
            sname = request.POST.get('staffname')
            pswd = request.POST.get('password')
            staf = authenticate(username = sname, password=pswd)
            if staf is not None:
                return redirect('adminhome')
            else:
                messages.error(request,"username or password incorrect")

    return render(request,'adminlogin.html')