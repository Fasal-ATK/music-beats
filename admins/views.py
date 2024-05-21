import json
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .forms import CategoryForm, ProductForm, BrandForm
from .models import Category, Product, Brand, Coupon
from user_side.models import Users, Order, OrderItem, OrderAddress
# Create your views here.


#-------------------------------------------------- Admin_Login ----------------------------------------------------


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
    logout(request)
    return redirect('adminlogin')


#---------------------------------------------------User_Manager----------------------------------------------
 

@login_required(login_url='adminlogin')
def User_Manager(request):
    user = Users.objects.filter(is_staff=False).order_by('-id')
    context = { 'user' : user }
    return render(request,'user_manager.html',context)

def Block_User(request,id):
    user = Users.objects.get(id=id)
    user.is_blocked = not user.is_blocked
    user.save()
    return redirect('user-mng')


#-------------------------------------------------- Dashboard ---------------------------------------------------


@login_required(login_url='adminlogin')
def Dashboard(request):
    return render(request,'dashboard.html')
 

 #-------------------------------------------------- Product ----------------------------------------------------


@login_required(login_url='adminlogin')
def Product_Manager(request):
    product = Product.objects.all().order_by('-id')
    category = Category.objects.filter(is_listed=True)
    return render(request,'product_mng.html',{'product':product,'category':category,})


def Add_Product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES)
        if form.is_valid():
            title = form.cleaned_data['title']
            if Product.objects.filter(title=title).exists():
                messages.error(request,f"This Product '{title}' already exists")
            else:
                form.save()
                messages.success(request,f"Product '{title}' Added Successfully")
            return redirect('product')
    return redirect('product')


def Edit_Product(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product,id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST,request.FILES,instance=product)
        if form.is_valid():
            title = form.cleaned_data['title']
            if Product.objects.filter(title=title).exclude(id=product_id).exists():
                messages.error(request,f"Ther is already a product with the name '{title}' ")
                return redirect('product')
            else:
                form.save()
                messages.info(request,f"Product '{product}' Has been Edited")
    return redirect('product')


def List_Product(request,p_id):
    product = Product.objects.get(id=p_id)
    product.is_listed = not product.is_listed
    product.save()
    return redirect('product')


#------------------------------------------------ Category  -----------------------------------------------------


@login_required(login_url='adminlogin')
def Category_Manager(request):
    categories = Category.objects.all().order_by('-id')
    return render(request,'category_mng.html',{'categories' : categories})


def Add_Category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            c_name = form.cleaned_data['name']
            if Category.objects.filter(name = c_name).exists():
                messages.error(request,f"Category '{c_name}' already exists")
            else:
                form.save()
                messages.success(request,f"'{c_name}' named category created successfully")
            return redirect('category')
    else:
        form = CategoryForm()
    return redirect('category')


def Edit_Category(request):
    if request.method == 'POST':
        c_id = request.POST.get('id')
        category = get_object_or_404(Category, id=c_id)
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            c_name = form.cleaned_data['name']
            if Category.objects.filter(name=c_name).exclude(id=c_id).exists():
                messages.error(request, f"Category '{c_name}' already exists ")
            else:
                form.save()
                messages.info(request, f"Category '{c_name}' has been edited ")
        return redirect('category')
    else:
        form = CategoryForm()
    return redirect('category',{'form': form})


def List_Category(request,c_id):
    category = Category.objects.get(id=c_id)
    category.is_listed = not category.is_listed
    category.save()
    return redirect('category')


# -------------------------------------------------- Brand -------------------------------------------------


def Brand_Manager(request):
    brands = Brand.objects.all().order_by('id')
    return render(request,'brand.html',{'brands':brands})


def Add_Brand(request):
    b_id = request.POST.get('id')
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            b_name = form.cleaned_data['name']
            if Brand.objects.filter(name=b_name).exists():
                messages.error(request,f"Brand with '{b_name}' already exists ")
            else:
                form.save()
                messages.success(request,f" Brand '{b_name}' has been created ")
            return redirect('brand')
    else:
        form = BrandForm()
    return render('brand', {'form': form})


def Edit_Brand(request):
    b_image = Brand.objects.values_list('image',flat=True)
    if request.method == 'POST':
        b_id = request.POST.get('id')
        brand = get_object_or_404(Brand, id = b_id)
        form = BrandForm(request.POST, instance = brand)
        if form.is_valid():
            b_name = form.cleaned_data['name']
            if Brand.objects.filter(name=b_name).exclude(id=b_id).exists():
                messages.error(request,f"Brand with '{b_name}' already exists ")
            else:
                form.save() 
                messages.success(request,f"Brand '{b_name}' has been Edited ")
                return redirect('brand')
    else:
        form = CategoryForm()
    return redirect('brand',{'form':form})


def List_Brand(request,b_id):
    brand = Brand.objects.get(id = b_id)
    brand.is_listed = not brand.is_listed
    brand.save()
    return redirect('brand')


# -------------------------------------------------- order -------------------------------------------------

def Order_Manager(request):
    orders = Order.objects.all().order_by('-id')
    return render(request, 'order_manager.html', {'orders': orders})


@csrf_exempt
def Update_Order_Status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            status = data.get('status')

            try:
                order = Order.objects.get(id=order_id)
                order.order_status = status
                order.save()
                return JsonResponse({'success': True})
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Order not found.'})
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def Orders_Detail(request, order_id):
    try:
        order = Order.objects.select_related('user', 'address').get(id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        order_address = OrderAddress.objects.get(order=order)
        context = {
            'order': order,
            'order_items': order_items,
            'order_address': order_address
        }
        return render(request, 'orders_details.html', context)
    except Order.DoesNotExist:
        return HttpResponseNotFound("Order not found")
    except OrderAddress.DoesNotExist:
        return HttpResponseNotFound("Order address not found")
    

# -------------------------------------------------- Coupon -------------------------------------------------


def Coupon_Manager(request):
    coupons = Coupon.objects.all()
    return render(request, 'coupon.html', {'coupons': coupons})

@csrf_protect
def Add_Coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code')
        expire_date = request.POST.get('expire_date')
        discount_price = request.POST.get('discount_price')
        minimum_amount = request.POST.get('minimum_amount')
        active = 'active' in request.POST
        
        expire_date = timezone.make_aware(datetime.strptime(expire_date, "%Y-%m-%dT%H:%M"))

        try:
            coupon = Coupon(
                coupon_code=coupon_code,
                expire_date=expire_date,
                discount_price=discount_price,
                minimum_amount=minimum_amount,
                active=active
            )
            coupon.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})