from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages

from .forms import CategoryForm,ProductForm
from .models import Category,Product
from user_side.models import Users
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache


# Create your views here.


@login_required(login_url='adminlogin')
def User_Manager(request):
    user = Users.objects.filter(is_staff=False).order_by('-id')
    context = { 'user' : user }
    return render(request,'user_manager.html',context)


@login_required(login_url='adminlogin')
def Dashboard(request):
    return render(request,'dashboard.html')


@never_cache
def Admin_Login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dash')
    if request.method == 'POST':
        sname = request.POST.get('staffname')
        pswd = request.POST.get('password')
        staf = authenticate(username = sname, password=pswd)
        if staf is not None and staf.is_staff:
            login(request,staf)
            return redirect('dash')
        else:
            messages.error(request,"username or password incorrect")
    return render(request,'adminlogin.html')


@never_cache
def Admin_Logout(request):
    logout(request,)
    return redirect('adminlogin')

def Block_User(request,id):
    user = Users.objects.get(id=id)
    user.is_blocked = not user.is_blocked
    user.save()
    return redirect('user-mng')


          #-------- product  --------


@login_required(login_url='adminlogin')
def Product_Manager(request):
    product = Product.objects.all().order_by('-id')
    
    return render(request,'product_mng.html',{'product':product})

def Add_Product(request):
    category = Category.objects.filter(is_listed=True)
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product')
    else:
        form = ProductForm()
        return render(request,'category_mng.html',{'form':form , 'category':category})







@login_required(login_url='adminlogin')
def Category_Manager(request):
    categories = Category.objects.all().order_by('-id')
    return render(request,'category_mng.html',{'categories' : categories})

def Add_Category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('category')
    else:
        form = CategoryForm()
    return redirect( 'category')

def Edit_Category(request):
    if request.method == 'POST':
        c_id = request.POST.get('id')
        category = get_object_or_404(Category, id = c_id)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('category')
    else:
        form = CategoryForm()
    return redirect('category') 

def List_Category(request,c_id):
    category = Category.objects.get(id=c_id)
    category.is_listed = not category.is_listed
    category.save()
    return redirect('category')