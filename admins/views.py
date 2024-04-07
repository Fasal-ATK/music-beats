from django.shortcuts import render,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from user_side.models import Users
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
# Create your views here.

@login_required(login_url='adminlogin')
def AdminHome(request):
    user = Users.objects.filter(is_staff=False)
    context = { 'user' : user }
    return render(request,'user_manager.html',context)

def Dashboard(request):
    return render(request,'dashboard.html')


def AdminLogin(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('usermanager')
    if request.method == 'POST':
        sname = request.POST.get('staffname')
        pswd = request.POST.get('password')
        staf = authenticate(username = sname, password=pswd)
        if staf is not None and staf.is_staff:
            login(request,staf)
            return redirect('usermanager')
        else:
            messages.error(request,"username or password incorrect")

    return render(request,'adminlogin.html')

def AdminLogout(request):
    logout(request,)
    return redirect('adminlogin')

def BlockUser(request,id):
    user = Users.objects.get(id=id)
    user.is_blocked = not user.is_blocked
    user.save()
    return redirect('usermanager')

# ----------------------------------------------------------------------------------------------------------------

            #-------- product
def ProductManager(request):
    return render(request,'product_mng.html')

def CategoryManager(request):
    return render(request,'category_mng.html')