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

# Dynamic Homestay Feature model
class HomestayFeature(models.Model):
    FEATURE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Yes/No'),
    ]
    homestay = models.ForeignKey(Homestay, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=FEATURE_TYPE_CHOICES)
    value = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.homestay.name} - {self.name} ({self.type})"

# Room model
class Room(models.Model):
    homestay = models.ForeignKey('Homestay', on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50) # Can be '1', 'A', 'Suite 101'
    capacity = models.IntegerField()
    is_under_maintenance = models.BooleanField(default=False, help_text='True = Under Maintenance, False = Not Under Maintenance')
    # Add other room-specific fields like description, amenities, etc.
    def __str__(self):
        return f"{self.homestay.name} - Room {self.room_number}"
    @property
    def get_status_display(self):
        return 'Under Maintenance' if self.is_under_maintenance else 'Not Under Maintenance'
    @property
    def get_status_class(self):
        return 'status-maintenance' if self.is_under_maintenance else 'status-available'
    # NOTE: After this change, run makemigrations and migrate, and update old data accordingly.

# Booking model
class Booking(models.Model):
    BOOKING_SOURCE_CHOICES = [
        ('registration', 'Registration'),
        ('calendar', 'Calendar'),
    ]
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
    source = models.CharField(max_length=20, choices=BOOKING_SOURCE_CHOICES, default='registration')
    class Meta:
        pass  # Only one Meta class, no unique_together
    def __str__(self):
        return f"{self.homestay.name} - {self.date} - {self.status}"


