from django.contrib import admin

from .models import Homestay, Room, Booking
from .admin_custom_user import *


@admin.register(Homestay)
class HomestayAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'address']
    search_fields = ['name', 'owner__username']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['homestay', 'room_number', 'capacity', 'is_under_maintenance']
    list_filter = ['is_under_maintenance', 'homestay']
    search_fields = ['room_number', 'homestay__name']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['homestay', 'date', 'status', 'guest_name', 'num_people']
    list_filter = ['status', 'homestay', 'date']
    search_fields = ['guest_name', 'homestay__name']
    date_hierarchy = 'date'
