from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random
from django.contrib.auth.decorators import login_required
from django.http import  HttpResponse, JsonResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template.loader import render_to_string

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

import razorpay  
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist

from user_side.models import CouponUsage, Users, Cart, CartItem, Address, Order, OrderItem, OrderAddress, Wallet, WalletHistory, Wishlist
from admins.models import Coupon, Product, Category
from user_side.forms import AddressForm




#------------------------------------- Signup / Login / OTP ------------------------------

# Utility function to send OTP email
def send_otp_email(email, otp):
    send_mail(
        'Verification Code',
        f'Your OTP is: {otp}',
        'fasalrahmanatk706@gmail.com',
        [email],
        fail_silently=False,
    )

# Home page view
@never_cache
def UserHome(request):
    product = Product.objects.filter(is_listed=True)
    category = Category.objects.filter(is_listed=True)
    return render(request, 'index.html', {'product': product, 'category': category})

# Signup view
@never_cache
def Signup(request):
    if request.method == 'POST':
        uname = request.POST.get('uname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass')
        pass2 = request.POST.get('re_pass')
        if len(pass1) < 8:
            messages.error(request, "Password needs to be 8 or more characters")
        elif len(pass1) > 25:
            messages.error(request, "Password is too long")
        elif pass1 != pass2:
            messages.error(request, "Passwords do not match")
        elif not uname.isalnum():
            messages.error(request, "Username is not allowed")
        elif Users.objects.filter(username=uname).exists():
            messages.error(request, 'Username already exists')
        elif Users.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
        else:
            otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            request.session['signup_otp'] = otp
            request.session['signup_email'] = email
            send_otp_email(email, otp)
            request.session['signup_user_details'] = {
                'uname': uname,
                'phone': phone,
                'email': email,
                'pass': pass1,
            }
            return redirect('verify_otp')
    return render(request, 'signup.html')

# OTP verification view
def Verify_OTP(request):
    if request.method == 'POST':
        if 'signup_otp' in request.session and 'signup_email' in request.session:
            otp = request.POST.get('combined-otp')
            if otp == str(request.session['signup_otp']):
                user_details = request.session.pop('signup_user_details')
                new_user = Users.objects.create_user(
                    username=user_details['uname'], 
                    email=user_details['email'],
                    password=user_details['pass'], 
                    phone=user_details['phone']
                )
                new_user.save()
                Wallet.objects.create(user=new_user)
                messages.success(request, "Account created successfully. You can now login.")
                return redirect('ulogin')
            else:
                messages.error(request, "Invalid OTP. Please try again.")
                return redirect('signup')
        else:
            messages.error(request, "Session expired. Please try again.")
            return redirect('signup')
    return render(request, 'otp.html')

# Login view
@never_cache
def Login(request):
    if request.user.is_authenticated and not request.user.is_staff:
        return redirect('home')
    if request.method == 'POST':
        uname = request.POST.get('username')
        pswrd = request.POST.get('password')
        user = authenticate(request, username=uname, password=pswrd)
        if user:
            login(request, user)
            return redirect('adminhome/' if request.user.is_staff else 'home')
        else:
            messages.error(request, "Username or password incorrect")
    return render(request, 'login.html')

# Logout view
@never_cache
def Logout(request):
    logout(request)
    return redirect('ulogin')

# Shop view
def Shop(request):
    product = Product.objects.filter(is_listed=True)
    category = Category.objects.filter(is_listed=True)

    # Get sorting and category filter parameters from the request
    sort_by = request.GET.get('sort_by')
    selected_category = request.GET.get('category')

    # Apply category filter if a category is selected
    if selected_category:
        product = product.filter(category__id=selected_category)

    # Apply sorting based on the sort_by parameter
    if sort_by == 'name_asc':
        product = product.order_by('title')
    elif sort_by == 'name_desc':
        product = product.order_by('-title')
    elif sort_by == 'price_asc':
        product = product.order_by('price')
    elif sort_by == 'price_desc':
        product = product.order_by('-price')

    return render(request, 'shop.html', {'product': product, 'category': category, 'sort_by': sort_by, 'selected_category': selected_category})


# Single product view
def Single_Product(request, id):
    product = get_object_or_404(Product, id=id)
    related_product = Product.objects.filter(category = product.category)
    return render(request, 'single-product.html', {'product': product,'related_product':related_product})

def get_product_details(request):
    if request.method == 'GET' and request.is_ajax():
        product_id = request.GET.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        # Assuming you have a template named 'product_details.html' to render the product details
        html = render_to_string('product_details.html', {'product': product})
        return JsonResponse({'html': html})
    else:
        return JsonResponse({'error': 'Invalid request'})
#------------------------------------------- Cart -----------------------------

# Cart view
@login_required(login_url='ulogin')
def Cart_Page(request):
    if 'coupon_applied' in request.session:
        del request.session['coupon_applied']
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).order_by('-id')
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    # Get discounted price from session if available
    discounted_price = request.session.get('discounted_price', total_price)

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discounted_price': discounted_price,
    })

# Add cart
@login_required(login_url='ulogin')
def Add_Cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if product.stock == 0:
        messages.error(request, f" '{product.title}' is out of stock ")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created and cart_item.quantity < product.stock:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, "Product added to cart successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# Remove cart
@login_required(login_url='ulogin')
def Remove_Cart(request, cartitem_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            cart_item = CartItem.objects.get(id=cartitem_id)
            cart_item.delete()
            cart = cart_item.cart
            cart_items = CartItem.objects.filter(cart=cart)
            total_price = sum(item.product.price * item.quantity for item in cart_items)
            # Remove coupon session data if items are removed
            request.session.pop('discounted_price', None)
            request.session.pop('coupon_code', None)
            return JsonResponse({'success': True, 'total_price': total_price})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item does not exist'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required(login_url='ulogin')
def Update_Cart(request, cartitem_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            cart_item = CartItem.objects.get(id=cartitem_id)
            new_quantity = int(request.POST.get('qty'))
            if 1 <= new_quantity <= 10:  # Check if quantity is within allowed range
                if new_quantity <= cart_item.product.stock:  # Check if quantity is within available stock
                    cart_item.quantity = new_quantity
                    cart_item.save()
                    cart = cart_item.cart
                    cart_items = CartItem.objects.filter(cart=cart)
                    total_price = sum(item.product.price * item.quantity for item in cart_items)
                    item_total = cart_item.product.price * cart_item.quantity
                    return JsonResponse({'success': True, 'total_price': total_price, 'item_total': item_total})
                else:
                    return JsonResponse({'success': False, 'message': 'Quantity exceeds available stock'})
            else:
                return JsonResponse({'success': False, 'message': 'Quantity must be between 1 and 10'})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item does not exist'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})



#---------------------------------------------  Checkout_Page ------------------------------------


@login_required(login_url='ulogin')
def Product_Checkout(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        return redirect('cart')

    total_price = sum(item.product.price * item.quantity for item in cart_items)

    # Get the wallet balance or set it to 0 if no wallet exists
    try:
        user_wallet = Wallet.objects.get(user=request.user)
        user_wallet_balance = user_wallet.balance
    except Wallet.DoesNotExist:
        user_wallet_balance = Decimal(0)
    
    discount = Decimal(0)
    if 'coupon_applied' in request.session:
        coupon_details = request.session['coupon_applied']
        discount = Decimal(coupon_details['discount'])
    
    user_address = Address.objects.filter(user=request.user)
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'user_address': user_address,
        'user_wallet_balance':user_wallet_balance
    })


@login_required(login_url='ulogin')
def Apply_Coupon(request):
    print('get')
    if request.method == 'POST':
        print('post')
        coupon_code = request.POST.get('coupon_code')
        total_price = float(request.POST.get('total_price', 0))
        user = request.user
        try:
            coupon = Coupon.objects.get(coupon_code=coupon_code)
            if coupon.is_expired:
                return JsonResponse({'success': False, 'error': 'Coupon has expired.'})
            if not coupon.active:
                return JsonResponse({'success': False, 'error': 'Coupon is not activated yet.'})
            if total_price < coupon.minimum_amount:
                return JsonResponse({'success': False, 'error': 'Total amount does not meet minimum requirement.'})
            if CouponUsage.objects.filter(user=user, coupon=coupon).exists():
                return JsonResponse({'success': False, 'error': 'Coupon has already been used.'})

            discounted_price = total_price - coupon.discount_price
            discount = coupon.discount_price
            request.session['coupon_applied'] = {
                'discounted_price': discounted_price,
                'discount': discount,
                'coupon_code': coupon_code
            }
            return JsonResponse({'success': True, 'message': 'Coupon applied successfully!'})
        except Coupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Coupon not found.'})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})


@login_required(login_url='ulogin')
def Remove_Coupon(request):
    if request.method == 'POST':
        if 'coupon_applied' in request.session:
            del request.session['coupon_applied']
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'No coupon applied.'})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})


@login_required(login_url='ulogin')
def Place_Order(request):
    if request.method == 'POST':
        user_cart = Cart.objects.get(user=request.user)
        cart_items = CartItem.objects.filter(cart=user_cart)
        cart_total_price = sum(item.product.price * item.quantity for item in cart_items)
        payment_method = request.POST.get('payment_method')
        address_id = request.POST.get('address')
        address = get_object_or_404(Address, id=address_id)
        payment_status = request.POST.get('payment_status', 'pending')

        # Get coupon discount if applied
        discount = 0
        coupon_code = ''

        if 'coupon_applied' in request.session:
            coupon_data = request.session['coupon_applied']
            coupon_code = coupon_data['coupon_code']
            discount = coupon_data['discount']
            coupon = Coupon.objects.get(coupon_code=coupon_code)

        # Determine order status based on payment status
        if payment_status == 'success':
            order_status = 'order_placed'
        else:
            order_status = 'pending'

        # Wrap order creation in a transaction
        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=cart_total_price - discount,
                coupon_discount=discount,
                coupon_code=coupon_code,
                payment_method=payment_method,
                order_status=order_status
            )

            # Create the order items and update product quantities
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    price=item.product.price,
                    quantity=item.quantity
                )
                item.product.stock -= item.quantity  # Decrease product quantity
                item.product.save()

            # Create the order address
            OrderAddress.objects.create(
                order=order,
                name=address.name,
                phone=address.phone,
                address_line=address.address_line,
                city=address.city,
                state=address.state,
                postal_code=address.postal_code,
                country=address.country
            )

            # Remove coupon data from session if applied
            if 'coupon_applied' in request.session:
                coupon_data = request.session['coupon_applied']
                coupon_code = coupon_data['coupon_code']
                coupon = Coupon.objects.get(coupon_code=coupon_code)
                CouponUsage.objects.create(user=request.user, coupon=coupon)
                del request.session['coupon_applied']

            # Create wallet history record if payment is made through wallet
            if payment_method == 'wallet':
                wallet = get_object_or_404(Wallet, user=request.user)
                wallet.balance -= cart_total_price - discount  # Deduct the amount from the wallet balance
                wallet.save()
                WalletHistory.objects.create(
                    wallet=wallet,
                    amount=cart_total_price - discount,
                    transaction_type='debit',
                    description='Ordered a product'
                )

            # Clear the cart
            user_cart.cartitem_set.all().delete()

        if order_status == 'order_placed':
            messages.success(request, 'Order placed successfully. Thank you!')
        else:
            messages.warning(request, 'Payment failed. Your order is pending.')

        return redirect('order-page')

    return redirect('checkout')

def Complete_Pending_Order(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        print(order_id)
        try:
            print('try')
            order = get_object_or_404(Order, id=order_id)
            order.order_status = 'order_placed'
            order.save()
            return JsonResponse({'status': 'success', 'message': 'Order status updated successfully.'})
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Order not found.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


#-------------------------------------------- Whishlist ---------------------------------------


#Wishlist
@login_required(login_url='ulogin')
def Wishlist_Page(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'wishlist_items': wishlist_items})

#Add wishlist
@login_required(login_url='ulogin')
def Add_Wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request, "Product added to wishlist successfully.")
    else:
        messages.info(request, "Product is already in your wishlist.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

# Remove wishlist
@login_required(login_url='ulogin')
def Remove_Wishlist(request, wishlistitem_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            wishlist_item = Wishlist.objects.get(id=wishlistitem_id, user=request.user)
            wishlist_item.delete()
            return JsonResponse({'success': True})
        except Wishlist.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Wishlist item does not exist'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})



#-------------------------------------  Profile ------------------------------


@login_required(login_url='ulogin')
def User_Profile(request):
    user_address = Address.objects.filter(user=request.user)
    wallet = get_object_or_404(Wallet, user=request.user)  # Fetch the wallet object
    history = WalletHistory.objects.filter(wallet=wallet)
    return render(request, 'profile.html', {'user_address': user_address, 'wallet': wallet, 'history': history})


# Add address view
@login_required(login_url='ulogin')
def Add_Address(request):
    address_limit = 6 
    address_count = Address.objects.filter(user=request.user).count()
    if address_count >= address_limit:
        messages.error(request, "Address limit reached. You cannot add more addresses.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
    return redirect(request.META.get('HTTP_REFERER', '/'))

# Edit address view
@login_required(login_url='ulogin')
def Edit_Address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True}) 
        return JsonResponse({'errors': form.errors}, status=400)
    form = AddressForm(instance=address)
    data = {
        'id': address.id,
        'name': address.name,
        'address_line': address.address_line,
        'phone': address.phone,
        'city': address.city,
        'state': address.state,
        'postal_code': address.postal_code,
        'country': address.country,
    }
    return JsonResponse(data)

# Delete address view
@login_required(login_url='ulogin')
def Delete_Address(request, address_id):
    if request.method == 'POST':
        try:
            address = Address.objects.get(id=address_id)
            address.delete()
            return JsonResponse({'message': 'Address deleted successfully'}, status=200)
        except Address.DoesNotExist:
            return JsonResponse({'error': 'Address does not exist'}, status=404)


# Change password view
@never_cache
def Change_Password(request):
    if request.method == 'POST':
        current_pass = request.POST.get("current_password")
        new_pass = request.POST.get("new_password")
        confirm_pass = request.POST.get("confirm_new_password")
        if new_pass != confirm_pass:
            messages.error(request, 'Confirmation password does not match')
            return redirect('profile')
        user = request.user
        if user.check_password(current_pass):
            user.set_password(new_pass)
            user.save()
            logout(request)
            messages.success(request, 'Password changed successfully')
        else:
            messages.error(request, 'Incorrect current password')
    return redirect('profile')


@login_required(login_url='ulogin')
def Add_Wallet_Money(request):
    if request.method == 'POST':
        user_wallet = get_object_or_404(Wallet, user=request.user)
        money = int(request.POST.get('amount'))  # Ensure money is converted to an integer
        
        # Update wallet balance
        user_wallet.balance += money
        user_wallet.save()

        # Create wallet history record
        WalletHistory.objects.create(
            wallet=user_wallet,
            amount=money,
            transaction_type='credit',
            description='Money added to wallet'
        )
    return redirect('profile')
#-------------------------------------  Order_Page ------------------------------


# Order page view
@login_required(login_url='ulogin')
def Order_Page(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-id')
    return render(request, 'order.html', {'user_orders': user_orders})

@login_required(login_url='ulogin')
def Order_Details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    order_address, _ = OrderAddress.objects.get_or_create(order=order)

    can_cancel_order = order.order_status in ['order_placed', 'shipped', 'out_for_delivery']
    
    is_order_older_than_week = (timezone.now() - order.order_date) > timedelta(weeks=1)

    # Calculate the actual price
    actual_price = order.total_price + order.coupon_discount
    
    return render(request, 'order_details.html', {
        'order': order,
        'order_items': order_items,
        'order_address': order_address,
        'can_cancel_order': can_cancel_order,
        'actual_price': actual_price,
        'is_order_older_than_week': is_order_older_than_week,
    })

@login_required(login_url='ulogin')
def generate_invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    order_address = get_object_or_404(OrderAddress, order=order)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    pdf = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Invoice Header
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(30, height - 50, "Invoice")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, height - 70, f"Order ID: {order.id}")
    pdf.drawString(30, height - 90, f"Order Date: {order.order_date}")

    # From Address
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, height - 130, "From")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(30, height - 150, "Music Beats")
    pdf.drawString(30, height - 170, "Kerala, Calicut")
    pdf.drawString(30, height - 190, "Kozhikode, Mankavu")
    pdf.drawString(30, height - 210, "India")
    pdf.drawString(30, height - 230, "Phone: (123) 456-7890")
    pdf.drawString(30, height - 250, "Email: email@domain.com")

    # Billing Address
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(300, height - 130, "Bill To")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(300, height - 150, order.user.username)
    pdf.drawString(300, height - 170, order_address.address_line)
    pdf.drawString(300, height - 190, f"{order_address.city}, {order_address.state}")
    pdf.drawString(300, height - 210, order_address.postal_code)
    pdf.drawString(300, height - 230, order_address.country)
    pdf.drawString(300, height - 250, f"Phone: {order_address.phone}")
    pdf.drawString(300, height - 270, f"Email: {order.user.email}")

    # Order Items
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(30, height - 300, "Order Items")
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, height - 320, "Qty")
    pdf.drawString(80, height - 320, "Product")
    pdf.drawString(300, height - 320, "Unit Price")
    pdf.drawString(450, height - 320, "Total")

    pdf.setFont("Helvetica", 12)
    y = height - 340
    for item in order_items:
        pdf.drawString(30, y, str(item.quantity))
        pdf.drawString(80, y, item.product.title)
        pdf.drawString(300, y, f"₹{item.product.price}")
        pdf.drawString(450, y, f"₹{item.price}")
        y -= 20

    # Total
    y -= 20
    pdf.drawString(300, y, "Subtotal")
    pdf.drawString(450, y, f"₹{order.total_price + order.coupon_discount}")
    
    if order.coupon_discount > 0:
        y -= 20
        pdf.drawString(300, y, "Coupon Discount")
        pdf.drawString(450, y, f"-₹{order.coupon_discount}")

    y -= 20
    pdf.drawString(300, y, "Total")
    pdf.drawString(450, y, f"₹{order.total_price}")

    pdf.showPage()
    pdf.save()
    return response

# Order Cancelling view
@login_required(login_url='ulogin')
def Order_Cancelling(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Determine if the order can be canceled
    can_cancel_order = False
    if order.order_status in ['order_placed', 'shipped', 'out_for_delivery']:
        can_cancel_order = True

    # Cancel order logic
    if can_cancel_order:
        if order.payment_method in ['razor_pay', 'wallet']:
            user_wallet, created = Wallet.objects.get_or_create(user=request.user)

            with transaction.atomic():
                user_wallet.balance += order.total_price
                user_wallet.save()
        # Create wallet history record if payment is made through wallet
                WalletHistory.objects.create(
                wallet=user_wallet,
                amount=order.total_price,
                transaction_type='credit',
                description='Ordered Canceled')

        order.order_status = 'canceled'
        order.save()
        
        messages.success(request, 'Order canceled successfully')
    else:
        messages.error(request, 'Cannot cancel order')

    return redirect('order-details', order_id=order.id)

@login_required(login_url='ulogin')
def Return_Products(request, order_id):
    if request.method == 'POST':
        order_request = get_object_or_404(Order, id=order_id)
        order_request.order_status = 'return_requested'
        order_request.save()
        messages.success(request, 'Return request submitted successfully.')
    else:
        messages.error(request, 'Invalid request method.')
    return redirect('order-page')
