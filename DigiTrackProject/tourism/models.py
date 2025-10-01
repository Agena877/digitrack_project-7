from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Custom user model
class CustomUser(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)  # <--- restore this line
    first_name = None
    last_name = None
    def __str__(self):
        return self.username if not self.name else self.name

# UserProfile model
class UserProfile(models.Model):
    user = models.OneToOneField('tourism.CustomUser', on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=255)
    def __str__(self):
        return self.name or self.user.username

# Homestay model
class Homestay(models.Model):
    owner = models.ForeignKey('tourism.CustomUser', on_delete=models.CASCADE, related_name='homestays')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    # Homestay features fields
    max_guests = models.PositiveIntegerField(default=4)
    wifi_available = models.BooleanField(default=True)
    videoke_available = models.BooleanField(default=False)
    pet_friendly = models.BooleanField(default=False)
    beach_front = models.BooleanField(default=False)

    # Add other homestay-specific fields like contact info, description, etc.
    def __str__(self):
        return self.name

# Room model
class Room(models.Model):
    ROOM_STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
        ('occupied', 'Occupied'),
        ('maintenance', 'Under Maintenance'),
    ]
    homestay = models.ForeignKey('Homestay', on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50) # Can be '1', 'A', 'Suite 101'
    capacity = models.IntegerField()
    # room_type and price_per_night removed
    status = models.CharField(max_length=50, choices=ROOM_STATUS_CHOICES, default='available')
    # Add other room-specific fields like description, amenities, etc.
    def __str__(self):
        return f"{self.homestay.name} - Room {self.room_number}"
    @property
    def get_status_class(self):
        if self.status == 'available':
            return 'status-available'
        elif self.status == 'reserved':
            return 'status-reserved'
        elif self.status == 'occupied':
            return 'status-occupied'
        elif self.status == 'maintenance':
            return 'status-maintenance'
        return '' # Default or unknown status

# Booking model
class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('available', 'Available'),
        ('reserved', 'Reserved'),
    ]
    homestay = models.ForeignKey('Homestay', on_delete=models.CASCADE, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='available')
    guest_name = models.CharField(max_length=255, blank=True, null=True)
    num_people = models.IntegerField(blank=True, null=True)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        pass  # Only one Meta class, no unique_together
    def __str__(self):
        return f"{self.homestay.name} - {self.date} - {self.status}"


