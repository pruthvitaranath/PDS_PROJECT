from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_page, name='login'),  # URL for login page
    path('api/login/', views.login, name='login-backend'),  # Backend login API

    path('register/', views.register_page, name='register'),  # URL for register page
    path('api/register/', views.register, name='register-backend'),  # Backend register API

    path('item-details/', views.item_details_page, name='item-details'),  # URL for item details page
    path('api/item/<int:item_id>/', views.find_single_item, name='item-details-backend'),  # Backend item details API

    path('order-details/', views.order_details_page, name='order-details'),  # URL for order details page
    path('api/order/<int:order_id>/', views.find_order_items, name='order-details-backend'),  # Backend order details API

    path('accept-donation/', views.accept_donation_page, name='accept_donation'),  # URL for accept donation page
    path('api/accept-donation/', views.accept_donation, name='accept_donation_backend'),  # Backend accept donation API


    path('start-order/', views.start_order_page, name='start_order'),
    path('api/start-order/', views.start_order, name='start_order_backend'),

    path('add-to-order/', views.add_to_order_page, name='add_to_order'),
    path('api/add-to-order/', views.add_to_order, name='add_to_order_backend'),  

    path('prepare-order/', views.prepare_order_page, name='prepare_order'),
    path('api/prepare-order/', views.prepare_order, name='prepare_order_backend'),

    path('api/search-orders/', views.search_orders, name='search_orders'),

    path('update-order-status/', views.update_order_status_page, name='update_order_status'),
    path('api/update-order-status/', views.update_order_status, name='update_order_status_backend'),

    path('staff-dashboard/', views.staff_dashboard_page, name='staff_dashboard'),

]
