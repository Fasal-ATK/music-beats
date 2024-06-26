from . import views
from django.urls import path


urlpatterns = [

    path('adminlogin/',views.Admin_Login,name='adminlogin'),
    path('signout/',views.Admin_Logout,name='signout'),

    path('dash/',views.Dashboard,name='dash'),
    path('sales/',views.Sales,name='sales'),
    path('generate_sales_report/',views.Generete_Sales_Report, name='generate_sales_report'),

    path('user-mng/',views.User_Manager,name='user-mng'),
    path('block/<int:id>',views.Block_User,name='block'),
    
    path('category/',views.Category_Manager,name='category'),
    path('add-category/',views.Add_Category,name='add-category'),
    path('list-category/<int:c_id>',views.List_Category,name='list-category'),
    path('edit-category/',views.Edit_Category,name='edit-category'),
    
    path('product/', views.Product_Manager, name='product'),
    path('add-product/',views.Add_Product,name='add-product'),
    path('edit-product/',views.Edit_Product,name='edit-product'),
    path('list-product/<int:p_id>',views.List_Product,name='list-product'),

    path('brand/',views.Brand_Manager,name='brand'),
    path('add-brand/',views.Add_Brand,name='add-brand'),
    path('edit-brand/',views.Edit_Brand,name='edit-brand'),
    path('list-brand/<int:b_id>',views.List_Brand,name='list-brand'),

    path('orders/',views.Order_Manager,name='orders'),
    path('update-order-status/',views.Update_Order_Status,name='update-order-status'),
    path('orders-detail/<int:order_id>',views.Orders_Detail,name='orders-detail'),
    path('accept-reject/<int:order_id>/<str:action>/', views.Accept_or_Reject_Return, name='accept-reject'),
    path('refund/<int:order_id>/',views.Refund,name='refund'),

    path('coupons/', views.Coupon_Manager, name='coupons'),
    path('coupons/add/', views.Add_Coupon, name='add-coupon'),
    path('coupons/status/<int:coupon_id>/', views.Coupon_Status, name='coupon-status'),
    path('coupons/edit/', views.Edit_Coupon, name='edit-coupon'),
]

# fasal = 12345678