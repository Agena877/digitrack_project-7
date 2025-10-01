from django.urls import path
from . import views
from .views import api_register_tourist, api_my_tourist_chart_data
from .admin_log_api import admin_log_user_entries_api

urlpatterns = [
    path('api/tourist-chart-data/', views.api_tourist_chart_data, name='api_tourist_chart_data'),
    path('api/my-tourist-chart-data/', api_my_tourist_chart_data, name='api_my_tourist_chart_data'),
    path('api/tourist-list/', views.api_tourist_list, name='api-tourist-list'),
    path('api/my-tourists/', views.api_my_tourists, name='api_my_tourists'),
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('mto-admin/', views.admin_view, name='mto-admin'),
    path('register-tourist/', views.tourist_registration, name='register_tourist'),
    path('homestay/', views.homestay_view, name='homestay'),
    path('logout/', views.logout_view, name='logout'),
    path('api/booking/', views.booking_api, name='booking_api'),
    path('api/room/', views.room_api, name='room_api'),
    path('api/rooms/', views.room_list_api, name='room_list_api'),
    path('api/add_homestay_user/', views.add_homestay_user_api, name='add_homestay_user_api'),
    path('api/homestay_users/', views.homestay_user_list_api, name='homestay_user_list_api'),
    path('api/edit_homestay_user/', views.edit_homestay_user_api, name='edit_homestay_user_api'),
    path('api/admin_log_users/', admin_log_user_entries_api, name='admin_log_user_entries_api'),
    path('api/update_homestay_features/', views.update_homestay_features, name='update_homestay_features'),
    path('api/register-tourist/', api_register_tourist, name='api_register_tourist'),
]

