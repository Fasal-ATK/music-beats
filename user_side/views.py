from django.utils import timezone
from datetime import timedelta
import random
from django.contrib.auth.decorators import login_required
from django.http import  JsonResponse, HttpResponseRedirect
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.template.loader import render_to_string

import razorpay
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt

from user_side.models import CouponUsage, Users, Cart, CartItem, Address, Order, OrderItem, OrderAddress, Wallet, Wishlist
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

# Update cart
@login_required(login_url='ulogin')
def Update_Cart(request, cartitem_id):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            cart_item = CartItem.objects.get(id=cartitem_id)
            new_quantity = int(request.POST.get('qty'))
            if 1 <= new_quantity <= 10 and new_quantity <= cart_item.product.stock:
                cart_item.quantity = new_quantity
                cart_item.save()
                cart = cart_item.cart
                cart_items = CartItem.objects.filter(cart=cart)
                total_price = sum(item.product.price * item.quantity for item in cart_items)
                item_total = cart_item.product.price * cart_item.quantity
                # Remove coupon session data if cart is updated
                request.session.pop('discounted_price', None)
                request.session.pop('coupon_code', None)
                return JsonResponse({'success': True, 'total_price': total_price, 'item_total': item_total})
            else:
                return JsonResponse({'success': False, 'message': 'Quantity must be between 1 and 10 and within stock '})
        except CartItem.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cart item does not exist'})
    return JsonResponse({'success': False, 'message': 'Invalid request'})



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


# User profile view
@login_required(login_url='ulogin')
def User_Profile(request):
    user_address = Address.objects.filter(user=request.user)
    wallet = Wallet.objects.filter(user=request.user).values_list('balance', flat=True).first()
    return render(request, 'profile.html', {'user_address': user_address,'wallet':wallet})

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

@login_required(login_url='ulogin')
def Add_Wallet_Money(request):
    if request.method == 'POST':
        user_wallet = get_object_or_404(Wallet, user=request.user)
        money = request.POST.get('amount')
        user_wallet.balance += int(money)  # Ensure money is converted to an integer
        user_wallet.save()
    return redirect('profile')

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


#---------------------------------------------  Checkout_Page ------------------------------------

@login_required(login_url='ulogin')
def Product_Checkout(request):
    cart_items = CartItem.objects.filter(cart__user=request.user)
    if not cart_items.exists():
        return redirect('cart')

    total_price = sum(item.product.price * item.quantity for item in cart_items)
    
    user_address = Address.objects.filter(user=request.user)
    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'user_address': user_address
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

        # Get coupon discount if applied
        discount = 0
        coupon_code = ''

        if 'coupon_applied' in request.session:
            coupon_data = request.session['coupon_applied']
            coupon_code = coupon_data['coupon_code']
            discount = coupon_data['discount']
            coupon = Coupon.objects.get(coupon_code=coupon_code)

        # Wrap order creation in a transaction
        with transaction.atomic():
            # Create the order
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=cart_total_price - discount,
                coupon_discount=discount,
                coupon_code=coupon_code,
                payment_method=payment_method
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

            # Clear the cart
            user_cart.cartitem_set.all().delete()

        messages.success(request, 'Order placed successfully. Thank you!')
        return redirect('order-page')

    return redirect('checkout')


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

    # Determine if the order can be canceled
    can_cancel_order = order.order_status in ['order_placed', 'shipped', 'out_for_delivery']
    
    # Calculate if the order is older than one week
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
