#!/usr/bin/env python
"""
Script to create sample booking data for testing the date availability feature.
Run this script after setting up your Django environment:
python manage.py shell < create_sample_bookings.py
"""

import os
import sys
from datetime import datetime, timedelta

# Setup Django environment for direct script execution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DigiTrackProject.settings')
import django
django.setup()

from tourism.models import Homestay, Booking
from django.contrib.auth.models import User

def create_sample_bookings():
    print("Creating sample booking data...")
    
    # Get the first homestay, or create one if none exists
    try:
        homestay = Homestay.objects.first()
        if not homestay:
            # Create a sample user and homestay
            user, created = User.objects.get_or_create(
                username='homestay_owner',
                defaults={'password': 'testpass123', 'is_staff': False}
            )
            homestay = Homestay.objects.create(
                owner=user,
                name='Sample Homestay',
                address='123 Tourist Street, City'
            )
            print(f"Created sample homestay: {homestay.name}")
        
        # Clear existing bookings for this homestay
        Booking.objects.filter(homestay=homestay).delete()
        
        # Create sample bookings for the next 30 days
        today = datetime.now().date()
        sample_bookings = [
            # Available dates
            {'date': today + timedelta(days=1), 'status': 'available'},
            {'date': today + timedelta(days=2), 'status': 'available'},
            {'date': today + timedelta(days=4), 'status': 'available'},
            {'date': today + timedelta(days=6), 'status': 'available'},
            {'date': today + timedelta(days=8), 'status': 'available'},
            {'date': today + timedelta(days=10), 'status': 'available'},
            
            # Reserved dates with guest information
            {'date': today + timedelta(days=3), 'status': 'reserved', 'guest_name': 'Juan Dela Cruz', 'num_people': 3},
            {'date': today + timedelta(days=5), 'status': 'reserved', 'guest_name': 'Maria Santos', 'num_people': 2},
            {'date': today + timedelta(days=7), 'status': 'reserved', 'guest_name': 'Jose Rodriguez', 'num_people': 4},
            {'date': today + timedelta(days=9), 'status': 'reserved', 'guest_name': 'Ana Garcia', 'num_people': 1},
            {'date': today + timedelta(days=12), 'status': 'reserved', 'guest_name': 'Carlos Martinez', 'num_people': 5},
            {'date': today + timedelta(days=15), 'status': 'reserved', 'guest_name': 'Elena Fernandez', 'num_people': 2},
        ]
        
        for booking_data in sample_bookings:
            booking, created = Booking.objects.get_or_create(
                homestay=homestay,
                date=booking_data['date'],
                defaults={
                    'status': booking_data['status'],
                    'guest_name': booking_data.get('guest_name', ''),
                    'num_people': booking_data.get('num_people', 1),
                }
            )
            if created:
                print(f"Created booking: {booking.date} - {booking.status}")
            else:
                print(f"Booking already exists: {booking.date} - {booking.status}")
                
        print(f"Sample bookings created successfully for {homestay.name}!")
        print(f"Total bookings: {Booking.objects.filter(homestay=homestay).count()}")
        
    except Exception as e:
        print(f"Error creating sample bookings: {e}")

if __name__ == '__main__':
    create_sample_bookings()