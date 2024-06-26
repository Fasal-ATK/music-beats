import calendar
import json
from datetime import datetime,timedelta
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.db.models import Sum, Count

from .forms import CategoryForm, ProductForm, BrandForm
from .models import Category, Product, Brand, Coupon
from user_side.models import Users, Order, OrderItem, OrderAddress,Wallet, WalletHistory

from django.db import transaction

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

@login_required(login_url='adminlogin')
def Block_User(request,id):
    user = Users.objects.get(id=id)
    user.is_blocked = not user.is_blocked
    user.save()
    return redirect('user-mng')


#-------------------------------------------------- Dashboard ---------------------------------------------------

def Dashboard(request):
    top_products = OrderItem.objects.values('product__title').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:10]
    product_labels = [item['product__title'] for item in top_products]
    product_counts = [item['total_quantity'] for item in top_products]

    top_categories = OrderItem.objects.values('product__category__name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:10]
    category_labels = [item['product__category__name'] for item in top_categories]
    category_counts = [item['total_quantity'] for item in top_categories]

    orders = Order.objects.filter(order_status='completed')
    sales_by_month = orders.extra(select={'month': 'EXTRACT(month FROM order_date)'}).values('month').annotate(total_sales=Sum('total_price')).order_by('month')
    months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    sales_data = [0] * 12
    for sale in sales_by_month:
        sales_data[int(sale['month']) - 1] = float(sale['total_sales'])

    context = {
        'product_labels': json.dumps(product_labels),
        'product_counts': json.dumps(product_counts),
        'category_labels': json.dumps(category_labels),
        'category_counts': json.dumps(category_counts),
        'months': json.dumps(months),
        'sales_data': json.dumps(sales_data),
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='adminlogin')
def Sales(request):
    # Default to current month's data
    now = timezone.now()
    first_day_of_month = now.replace(day=1)
    start_date = first_day_of_month
    end_date = now

    if request.method == 'POST':
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')

        # Convert to timezone-aware datetimes
        start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)

    sales_data = Order.objects.filter(order_date__range=[start_date, end_date])

    # Calculate overall sales count, overall order amount, and overall discount
    overall_sales_count = sales_data.count()
    overall_order_amount = sum(order.total_price for order in sales_data)
    overall_discount = sum(order.coupon_discount for order in sales_data)

    # Prepare data for sales report
    sales_report = [{
        'order_id': order.id,
        'order_date': order.order_date,
        'total_price': order.total_price,
        'coupon_discount': order.coupon_discount,
    } for order in sales_data]

    if request.method == 'POST':
        return JsonResponse({
            'sales_report': sales_report,
            'overall_sales_count': overall_sales_count,
            'overall_order_amount': overall_order_amount,
            'overall_discount': overall_discount
        })

    return render(request, 'sales.html', {
        'overall_sales_count': overall_sales_count,
        'overall_order_amount': overall_order_amount,
        'overall_discount': overall_discount,
        'sales_report': sales_report,
    })


def Generete_Sales_Report(request):
    # Fetch sales data based on the selected date range or default to current month
    now = timezone.now()
    first_day_of_month = now.replace(day=1)
    start_date_str = request.GET.get('start_date', first_day_of_month.strftime('%Y-%m-%d'))
    end_date_str = request.GET.get('end_date', now.strftime('%Y-%m-%d'))

    start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
    end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)

    sales_data = Order.objects.filter(order_date__range=[start_date, end_date])

    # Calculate overall sales count, overall order amount, and overall discount
    overall_sales_count = sales_data.count()
    overall_order_amount = sum(order.total_price for order in sales_data)
    overall_discount = sum(order.coupon_discount for order in sales_data)

    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Draw a title
    p.drawString(100, height - 100, f"Sales Report from {start_date_str} to {end_date_str}")

    # Draw overall statistics
    p.drawString(100, height - 150, f"Overall Sales Count: {overall_sales_count}")
    p.drawString(100, height - 170, f"Overall Order Amount: {overall_order_amount}")
    p.drawString(100, height - 190, f"Overall Discount: {overall_discount}")

    # Draw table headers
    p.drawString(100, height - 230, "Order ID")
    p.drawString(200, height - 230, "Order Date")
    p.drawString(300, height - 230, "Total Price")
    p.drawString(400, height - 230, "Coupon Discount")

    # Draw table content
    y = height - 250
    for order in sales_data:
        p.drawString(100, y, str(order.id))
        p.drawString(200, y, order.order_date.strftime('%Y-%m-%d %H:%M'))
        p.drawString(300, y, str(order.total_price))
        p.drawString(400, y, str(order.coupon_discount))
        y -= 20
        if y < 100:  # Add a new page if space runs out
            p.showPage()
            y = height - 100

    # Close the PDF object cleanly.
    p.showPage()
    p.save()
    return response

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

@login_required(login_url='adminlogin')
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

@login_required(login_url='adminlogin')
def Order_Manager(request):
    orders = Order.objects.all().order_by('-id')
    completed_statuses = ['completed', 'canceled', 'return_requested', 'return_accepted', 'return_rejected', 'returned','pending']
    return render(request, 'order_manager.html', {'orders': orders, 'completed_statuses': completed_statuses})


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

@login_required(login_url='adminlogin')
def Orders_Detail(request, order_id):
    try:
        order = Order.objects.select_related('user', 'address').get(id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        order_address = OrderAddress.objects.get(order=order)

        # Calculate the total for each order item
        order_items_with_total = []
        for item in order_items:
            total_price = item.product.price * item.quantity
            order_items_with_total.append({
                'item': item,
                'total_price': total_price
            })
        sub_total = order.total_price + order.coupon_discount

        context = {
            'order': order,
            'order_items_with_total': order_items_with_total,
            'sub_total':sub_total,
            'order_address': order_address,
            'coupon_code': order.coupon_code,
            'coupon_discount': order.coupon_discount,
        }
        return render(request, 'orders_details.html', context)
    except Order.DoesNotExist:
        return HttpResponseNotFound("Order not found")
    except OrderAddress.DoesNotExist:
        return HttpResponseNotFound("Order address not found")

    
def Accept_or_Reject_Return(request, order_id, action):
    try:
        order = Order.objects.get(id=order_id)
        if action == 'accept':
            order.order_status = 'return_accepted'

        elif action == 'reject':
            order.order_status = 'return_rejected'
        
        order.save()
        return redirect('orders-detail', order_id=order_id)
    
    except Order.DoesNotExist:
        return HttpResponseNotFound("Order not found")


def Refund(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        user_wallet=get_object_or_404(Wallet,user=order.user)
        with transaction.atomic():
            user_wallet.balance += order.total_price
            user_wallet.save()

            #wallet history
            WalletHistory.objects.create(
                wallet=user_wallet,
                amount=order.total_price,
                transaction_type='credit',
                description='Return Order refunded'
                )

            order.order_status = 'returned'
            order.save()
        messages.success(request, "The order has been refunded successfully.")
        return redirect('orders-detail', order_id=order_id)
    
    # If the request method is not POST, redirect to the order details page
    messages.error(request, "Invalid request method.")
    return redirect('orders-detail', order_id=order_id)

# -------------------------------------------------- Coupon -------------------------------------------------

@login_required(login_url='adminlogin')
def Coupon_Manager(request):
    coupons = Coupon.objects.all().order_by('-id')
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


def Coupon_Status(request,coupon_id):
    coupon = Coupon.objects.get(id=coupon_id)
    coupon.active = not coupon.active
    coupon.save()
    return redirect('coupons')


@login_required(login_url='adminlogin')
@csrf_protect
def Edit_Coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        coupon_code = request.POST.get('coupon_code')
        expire_date = request.POST.get('expire_date')
        discount_price = request.POST.get('discount_price')
        minimum_amount = request.POST.get('minimum_amount')
        active = 'active' in request.POST
        
        expire_date = timezone.make_aware(datetime.strptime(expire_date, "%Y-%m-%dT%H:%M"))

        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon.coupon_code = coupon_code
            coupon.expire_date = expire_date
            coupon.discount_price = discount_price
            coupon.minimum_amount = minimum_amount
            coupon.active = active
            coupon.save()
            return JsonResponse({'success': True})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    if request.method == 'GET':
        coupon_id = request.GET.get('coupon_id')
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            data = {
                'id': coupon.id,
                'coupon_code': coupon.coupon_code,
                'expire_date': coupon.expire_date.strftime("%Y-%m-%d %H:%M:%S"),
                'discount_price': coupon.discount_price,
                'minimum_amount': coupon.minimum_amount,
                'active': coupon.active,
            }
            return JsonResponse({'success': True, 'coupon': data})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request'})