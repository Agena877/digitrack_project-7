from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.views.decorators.http import require_POST
# AJAX endpoint to delete a room
@csrf_exempt
@require_POST
def delete_room_api(request):
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        if not room_id:
            return JsonResponse({'success': False, 'error': 'Missing room ID.'}, status=400)
        room = Room.objects.get(id=room_id)
        # Instead of deleting, mark as under maintenance
        room.is_under_maintenance = True
        room.save()
        return JsonResponse({'success': True, 'room': {
            'id': room.id,
            'room_number': room.room_number,
            'capacity': room.capacity,
            'status': 'maintenance' if room.is_under_maintenance else 'not_maintenance'
        }})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@csrf_exempt
@require_POST
def update_room_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        room_number = data.get('room_number')
        capacity = data.get('capacity')
        status = data.get('status')
        if not room_id:
            return JsonResponse({'success': False, 'error': 'Missing room ID.'}, status=400)
        room = Room.objects.get(id=room_id)
        if room_number is not None:
            room.room_number = room_number
        if capacity is not None:
            room.capacity = capacity
        if status is not None:
            room.is_under_maintenance = (status == 'maintenance')
        room.save()
        return JsonResponse({'success': True, 'room': {
            'id': room.id,
            'room_number': room.room_number,
            'capacity': room.capacity,
            'status': 'maintenance' if room.is_under_maintenance else 'not_maintenance'
        }})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.http import JsonResponse

@login_required(login_url='/login/')
@csrf_exempt
@require_POST
def reserve_room_api(request):
    """
    Reserve a room for a specific date. Expects JSON: {room_id, date, guest_name, num_people, contact_number}
    """
    import json
    try:
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        date = data.get('date')
        guest_name = data.get('guest_name')
        num_people = data.get('num_people')
        contact_number = data.get('contact_number')
        if not (room_id and date and guest_name and num_people):
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        room = Room.objects.get(id=room_id)
        homestay = room.homestay
        # Check if already reserved
        if Booking.objects.filter(room=room, date=date, status='reserved').exists():
            return JsonResponse({'success': False, 'error': 'Room already reserved for this date.'}, status=409)
        booking = Booking.objects.create(
            homestay=homestay,
            room=room,
            date=date,
            status='reserved',
            guest_name=guest_name,
            num_people=num_people,
            contact_number=contact_number,
            source='calendar'
        )
        return JsonResponse({'success': True, 'booking_id': booking.id})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
@login_required(login_url='/login/')
@require_GET
def calendar_data_api(request):
    """
    Returns JSON with all rooms and their bookings for the current homestay owner.
    """
    try:
        homestay = Homestay.objects.get(owner=request.user)
        rooms = Room.objects.filter(homestay=homestay)
        bookings = Booking.objects.filter(homestay=homestay)
        # Build room list
        room_list = [
            {
                'id': room.id,
                'room_number': room.room_number,
                'capacity': room.capacity,
                'status': 'Under Maintenance' if room.is_under_maintenance else 'Not Under Maintenance',
                'is_under_maintenance': room.is_under_maintenance
            }
            for room in rooms
        ]
        # Build booking list
        booking_list = [
            {
                'id': booking.id,
                'room_id': booking.room.id if booking.room else None,
                'date': booking.date.strftime('%Y-%m-%d'),
                'status': booking.status,
                'guest_name': booking.guest_name,
                'num_people': booking.num_people,
                'contact_number': booking.contact_number
            }
            for booking in bookings
        ]
        return JsonResponse({'success': True, 'rooms': room_list, 'bookings': booking_list})
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
# API endpoint to get bookings for calendar (GET)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
@login_required(login_url='/login/')
@require_GET
def booking_list_api(request):
    homestay = Homestay.objects.get(owner=request.user)
    room_id = request.GET.get('room_id')
    qs = Booking.objects.filter(homestay=homestay)
    if room_id:
        qs = qs.filter(room_id=room_id)
    bookings = [
        {
            'id': b.id,
            'status': b.status,
            'guest_name': b.guest_name or '',
            'num_people': b.num_people or 1,
            'start': b.date.strftime('%Y-%m-%d'),
            'end': b.date.strftime('%Y-%m-%d'),
            'room_id': b.room.id if b.room else None
        }
        for b in qs
    ]
    return JsonResponse({'success': True, 'bookings': bookings})
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
@csrf_exempt
@require_POST
def update_homestay_feature_api(request):
    """
    Update a single dynamic homestay feature (name, type, value).
    """
    import logging
    logger = logging.getLogger('django')
    if not request.user.is_authenticated:
        logger.warning(f"[DEBUG] Update Feature failed: not authenticated")
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        feature_id = data.get('featureId')
        name = data.get('featureName')
        type_ = data.get('featureType')
        value = data.get('featureValue')
        logger.info(f"[DEBUG] Update Feature: user={request.user}, id={feature_id}, name={name}, type={type_}, value={value}")
        feature = HomestayFeature.objects.get(id=feature_id, homestay__owner=request.user)
        if name:
            feature.name = name
        if type_:
            feature.type = type_
        if value is not None:
            feature.value = value
        feature.save()
        logger.info(f"[DEBUG] Feature updated: id={feature.id}, value={feature.value}")
        return JsonResponse({'success': True})
    except HomestayFeature.DoesNotExist:
        logger.error(f"[DEBUG] Update Feature failed: Feature not found id={feature_id}")
        return JsonResponse({'success': False, 'error': 'Feature not found.'}, status=404)
    except Exception as e:
        logger.error(f"[DEBUG] Update Feature error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
# AJAX endpoint to delete a homestay feature
@csrf_exempt
@require_POST
def delete_homestay_feature_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        feature_id = data.get('featureId')
        if not feature_id:
            return JsonResponse({'success': False, 'error': 'Missing feature ID.'}, status=400)
        feature = HomestayFeature.objects.get(id=feature_id, homestay__owner=request.user)
        feature.delete()
        return JsonResponse({'success': True})
    except HomestayFeature.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Feature not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Sum
from .models import CustomUser, Homestay, Room, Booking
from .models import HomestayFeature

# AJAX endpoint to get all features for the current homestay
from django.views.decorators.http import require_GET
@require_GET
def get_homestay_features_api(request):
    import logging
    logger = logging.getLogger('django')
    if not request.user.is_authenticated:
        logger.warning(f"[DEBUG] Get Features failed: not authenticated")
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        homestay = Homestay.objects.get(owner=request.user)
        features = HomestayFeature.objects.filter(homestay=homestay)
        features_list = [
            {
                'id': f.id,
                'name': f.name,
                'type': f.type,
                'value': f.value
            } for f in features
        ]
        logger.info(f"[DEBUG] Get Features: user={request.user}, count={len(features_list)}")
        return JsonResponse({'success': True, 'features': features_list})
    except Homestay.DoesNotExist:
        logger.error(f"[DEBUG] Get Features failed: Homestay not found for user {request.user}")
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        logger.error(f"[DEBUG] Get Features error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
import json
import calendar
import datetime
from django.views.decorators.csrf import csrf_exempt

# AJAX endpoint to add a new homestay feature
@csrf_exempt
@require_POST
def add_homestay_feature_api(request):
    import logging
    logger = logging.getLogger('django')
    if not request.user.is_authenticated:
        logger.warning(f"[DEBUG] Add Feature failed: not authenticated")
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('featureName', '').strip()
        type_ = data.get('featureType', 'text')
        value = data.get('featureValue', '')
        logger.info(f"[DEBUG] Add Feature: user={request.user}, name={name}, type={type_}, value={value}")
        if not name or not type_:
            logger.warning(f"[DEBUG] Add Feature failed: missing required fields")
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        homestay = Homestay.objects.get(owner=request.user)
        feature = HomestayFeature.objects.create(homestay=homestay, name=name, type=type_, value=value)
        logger.info(f"[DEBUG] Feature created: id={feature.id}")
        return JsonResponse({
            'success': True,
            'feature': {
                'id': feature.id,
                'name': feature.name,
                'type': feature.type,
                'value': feature.value
            }
        })
    except Homestay.DoesNotExist:
        logger.error(f"[DEBUG] Add Feature failed: Homestay not found for user {request.user}")
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        logger.error(f"[DEBUG] Add Feature error: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# API for dashboard chart data (monthly/yearly tourist counts) for the logged-in homestay
@login_required(login_url='/login/')
@require_GET
def api_my_tourist_chart_data(request):
    import calendar
    import datetime
    now = datetime.date.today()
    year = int(request.GET.get('year', now.year))
    # Always start yearly chart at 2024
    min_year = 2024
    # Find the latest year with a booking for this homestay
    latest_booking = Booking.objects.filter(homestay__owner=request.user).order_by('-date').first()
    max_year = year
    if latest_booking:
        max_year = max(year, latest_booking.date.year)
    # For dropdowns, always show 2024 to max_year
    year_range = max_year - min_year + 1
    try:
        homestay = Homestay.objects.get(owner=request.user)
    except Homestay.DoesNotExist:
        return JsonResponse({'monthly': {}, 'yearly': {}, 'year': year, 'year_range': year_range})
    # Monthly aggregation for selected year
    monthly = Booking.objects.filter(homestay=homestay, date__year=year, num_people__gt=0)
    monthly = monthly.values_list('date__month').annotate(total=Sum('num_people'))
    monthly_dict = {calendar.month_abbr[m]: t for m, t in monthly}
    monthly_data = {calendar.month_abbr[m]: monthly_dict.get(calendar.month_abbr[m], 0) for m in range(1, 13)}
    # Yearly aggregation for all years from 2024 to max_year
    yearly = Booking.objects.filter(homestay=homestay, date__year__gte=min_year, num_people__gt=0)
    yearly = yearly.values_list('date__year').annotate(total=Sum('num_people'))
    yearly_dict = {str(y): t for y, t in yearly}
    yearly_data = {str(y): yearly_dict.get(str(y), 0) for y in range(min_year, max_year + 1)}
    return JsonResponse({
        'monthly': monthly_data,
        'yearly': yearly_data,
        'year': year,
        'year_range': year_range
    })
from django.http import JsonResponse
# Import login_required for view protection
from django.contrib.auth.decorators import login_required
# API endpoint for a homestay to get only their own tourists
from django.views.decorators.http import require_GET
@login_required(login_url='/login/')
@require_GET
def api_my_tourists(request):
    try:
        homestay = Homestay.objects.get(owner=request.user)
        # Only include bookings from registration form
        bookings = Booking.objects.filter(homestay=homestay, source='registration').order_by('-date')
        data = [
            {
                'guest_name': b.guest_name or '-',
                'contact_number': b.contact_number or '-',
                'homestay_name': homestay.name,
                'date': b.date.strftime('%Y-%m-%d'),
                'num_people': b.num_people or '-',
                'status': b.status
            }
            for b in bookings
        ]
        return JsonResponse(data, safe=False)
    except Homestay.DoesNotExist:
        return JsonResponse([], safe=False)
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
@csrf_exempt
@require_POST
def edit_homestay_user_api(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = (data.get('username') or '').strip()
        homestay_name = (data.get('homestayName') or '').strip()
        owner_name = (data.get('ownerName') or '').strip()
        address = (data.get('address') or '').strip()
        status = (data.get('status') or 'Active').strip()
        password = data.get('password')
        # Find user and homestay
        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
        homestay = Homestay.objects.filter(owner=user).first()
        if not homestay:
            return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
        # Update user fields
        if owner_name:
            # Some CustomUser implementations use 'name'
            if hasattr(user, 'name'):
                user.name = owner_name
            else:
                try:
                    parts = owner_name.split(None, 1)
                    if hasattr(user, 'first_name'):
                        user.first_name = parts[0]
                        user.last_name = parts[1] if len(parts) > 1 and hasattr(user, 'last_name') else getattr(user, 'last_name', '')
                except Exception:
                    pass
        if status is not None:
            user.is_active = True if str(status).lower() in ('active', 'true', '1') else False

        # Handle password change if provided
        if password:
            try:
                user.set_password(password)
            except Exception:
                # Fallback if CustomUser doesn't support set_password
                user.password = password

        user.save()
        # Update homestay fields
        homestay.name = homestay_name
        homestay.address = address
        homestay.save()
        return JsonResponse({'success': True, 'message': 'User and homestay updated.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Generic user edit API: update name and active status for any user (staff/admin or homestay owner)
@csrf_exempt
@require_POST
def edit_user_api(request):
    """
    Edit a user's basic info (name) and/or toggle active status.
    Accepts JSON: { username, name, status }
    If a homestay payload is present (homestayName/address), it will attempt to update the Homestay too.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = (data.get('username') or '').strip()
        name = (data.get('name') or data.get('ownerName') or '').strip()
        status = data.get('status')
        homestay_name = data.get('homestayName')
        address = data.get('address')

        if not username:
            return JsonResponse({'success': False, 'error': 'Missing username.'}, status=400)

        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        if name:
            # Some CustomUser implementations use 'name' field, otherwise try first/last
            if hasattr(user, 'name'):
                user.name = name
            else:
                # Attempt to split into first/last if available
                try:
                    parts = name.split(None, 1)
                    if hasattr(user, 'first_name'):
                        user.first_name = parts[0]
                        user.last_name = parts[1] if len(parts) > 1 and hasattr(user, 'last_name') else getattr(user, 'last_name', '')
                except Exception:
                    pass

        if status is not None:
            user.is_active = True if str(status).lower() in ('active', 'true', '1') else False

        # Handle password change if provided
        password = data.get('password')
        if password:
            try:
                user.set_password(password)
            except Exception:
                # Fallback to assigning raw password if set_password not available
                user.password = password

        user.save()

        # If homestay fields provided, update homestay if exists
        if homestay_name or address:
            homestay = Homestay.objects.filter(owner=user).first()
            if homestay:
                if homestay_name:
                    homestay.name = homestay_name
                if address:
                    homestay.address = address
                homestay.save()

        return JsonResponse({'success': True, 'username': user.username, 'status': 'Active' if user.is_active else 'Inactive'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.db.models import Sum
from django.views.decorators.http import require_GET

# API for dashboard chart data (monthly/yearly tourist counts)
@require_GET
def api_tourist_chart_data(request):
    from .models import Booking
    import calendar
    import datetime
    now = datetime.date.today()
    # Get params
    year = int(request.GET.get('year', now.year))
    year_range = int(request.GET.get('year_range', 5))
    # Monthly aggregation for selected year
    # Only consider bookings created via the registration (exclude calendar reservations)
    monthly = Booking.objects.filter(date__year=year, num_people__gt=0, source='registration')
    monthly = monthly.values_list('date__month').annotate(total=Sum('num_people'))
    monthly_dict = {calendar.month_abbr[m]: t for m, t in monthly}
    # Fill missing months with 0
    monthly_data = {calendar.month_abbr[m]: monthly_dict.get(calendar.month_abbr[m], 0) for m in range(1, 13)}
    # Yearly aggregation for last N years
    # Only include registration-sourced bookings (exclude calendar reservations)
    start_year = year - year_range + 1
    yearly = Booking.objects.filter(date__year__gte=start_year, num_people__gt=0, source='registration')
    yearly = yearly.values_list('date__year').annotate(total=Sum('num_people'))
    yearly_dict = {str(y): t for y, t in yearly}
    yearly_data = {str(y): yearly_dict.get(str(y), 0) for y in range(start_year, year + 1)}
    return JsonResponse({
        'monthly': monthly_data,
        'yearly': yearly_data,
        'year': year,
        'year_range': year_range
    })
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
# API endpoint for AJAX tourist table
@csrf_exempt
@require_GET
def api_tourist_list(request):
    from .models import Booking
    # Only include tourists that were created through the registration flow (exclude calendar reservations)
    bookings = Booking.objects.filter(num_people__gt=0, source='registration').order_by('-created_at').values(
        'guest_name', 'contact_number', 'homestay__name', 'date', 'num_people', 'status'
    )
    # Convert date to string
    data = []
    for b in bookings:
        d = dict(b)
        d['date'] = d['date'].isoformat() if d['date'] else ''
        data.append(d)
    # DEBUG: print to server log
    print('API /api/tourist-list/ returns:', data)
    return JsonResponse(data, safe=False)


# Server-side search for tourists (bookings created via registration)
@require_GET
def api_tourist_search(request):
    """Search tourists by guest name, contact number, or homestay name. Use ?q=..."""
    from .models import Booking
    q = (request.GET.get('q') or '').strip()
    # Base queryset: registration-sourced bookings
    bookings = Booking.objects.filter(num_people__gt=0, source='registration').order_by('-created_at')

    # If the caller is an authenticated homestay owner (not staff), restrict results
    # to that owner's homestay so homestay pages don't see other homestays' bookings.
    try:
        from .models import Homestay
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and not (user.is_staff or user.is_superuser):
            homestay = Homestay.objects.filter(owner=user).first()
            if homestay:
                bookings = bookings.filter(homestay=homestay)
    except Exception:
        # If anything goes wrong, fall back to global search (safe default)
        pass

    if q:
        bookings = bookings.filter(
            Q(guest_name__icontains=q) | Q(contact_number__icontains=q) | Q(homestay__name__icontains=q)
        )
    bookings = bookings.values('guest_name', 'contact_number', 'homestay__name', 'date', 'num_people', 'status')
    data = []
    for b in bookings:
        d = dict(b)
        d['date'] = d['date'].isoformat() if d['date'] else ''
        data.append(d)
    return JsonResponse(data, safe=False)
@csrf_exempt
@require_POST
def api_register_tourist(request):
    data = json.loads(request.body.decode('utf-8'))
    required_fields = ['name', 'homestayName', 'contactNumber', 'region', 'province', 'city', 'barangay', 'dateArrival', 'dateDeparture', 'numTourist']
    for field in required_fields:
        if not data.get(field):
            return JsonResponse({'success': False, 'error': f'Missing required field: {field}'}, status=400)
    name = data['name']
    homestay_name = data['homestayName']
    contact = data['contactNumber']
    region = data['region']
    province = data['province']
    city = data['city']
    barangay = data['barangay']
    date_arrival = data['dateArrival']
    date_departure = data['dateDeparture']
    num_tourist = data['numTourist']
    try:
        homestay = Homestay.objects.get(name=homestay_name)
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    # Prevent registration if homestay owner is suspended
    if not homestay.owner.is_active:
        return JsonResponse({'success': False, 'error': 'Registration is not allowed. This homestay is currently suspended.'}, status=403)
    from datetime import datetime
    try:
        booking_date = datetime.strptime(date_arrival, '%Y-%m-%d').date()
    except Exception:
        return JsonResponse({'success': False, 'error': 'Invalid date.'}, status=400)
    # Prevent duplicate: same homestay and date (matches DB unique constraint)
    if Booking.objects.filter(homestay=homestay, date=booking_date).exists():
        return JsonResponse({'success': False, 'error': 'A booking for this homestay and date already exists. Please choose another date.'}, status=409)
    Booking.objects.create(
        homestay=homestay,
        date=booking_date,
        status='reserved',
        guest_name=name,
        num_people=num_tourist,
        contact_number=contact,
        source='registration'
    )
    return JsonResponse({'success': True, 'message': 'Tourist registered successfully!'})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
import time
from django.core.cache import cache
from django.urls import reverse
from .models import CustomUser, Homestay, Room, Booking
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test

# Tourist registration view
@login_required(login_url='/login/')
@csrf_exempt
def tourist_registration(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        homestay_name = request.POST.get('homestayName')
        contact = request.POST.get('contactNumber')
        region = request.POST.get('region')
        province = request.POST.get('province')
        city = request.POST.get('city')
        barangay = request.POST.get('barangay')
        date_arrival = request.POST.get('dateArrival')
        date_departure = request.POST.get('dateDeparture')
        num_tourist = request.POST.get('numTourist')
        # Find the homestay instance
        try:
            homestay = Homestay.objects.get(name=homestay_name)
        except Homestay.DoesNotExist:
            messages.error(request, 'Homestay not found.')
            return redirect('mto-admin')
        # Save as Booking (one per day)
        from datetime import datetime, timedelta
        try:
            start_date = datetime.strptime(date_arrival, '%Y-%m-%d').date()
            end_date = datetime.strptime(date_departure, '%Y-%m-%d').date()
        except Exception:
            messages.error(request, 'Invalid date.')
            return redirect('mto-admin')
        days = (end_date - start_date).days + 1
        for i in range(days):
            day = start_date + timedelta(days=i)
            Booking.objects.create(
                homestay=homestay,
                date=day,
                status='reserved',
                guest_name=name,
                num_people=num_tourist,
                source='registration'
            )
    messages.success(request, 'Tourist registered successfully!')
    # Add ?show=management to URL to activate the tab
    return redirect('/mto-admin/?show=management')
    return redirect('mto-admin')



# Update homestay features API
@login_required(login_url='/login/')
@require_POST
def update_homestay_features(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        homestay = Homestay.objects.get(owner=request.user)
        homestay.max_guests = int(data.get('max_guests', 4))
        homestay.wifi_available = bool(data.get('wifi_available', False))
        homestay.videoke_available = bool(data.get('videoke_available', False))
        homestay.pet_friendly = bool(data.get('pet_friendly', False))
        homestay.beach_front = bool(data.get('beach_front', False))
        homestay.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_GET
def homestay_user_list_api(request):
    try:
        # Only users with a homestay account
        homestays = Homestay.objects.select_related('owner').all()
        from django.db.models import Sum
        user_list = []
        for h in homestays:
            # Count total guests who booked this homestay
            total_guests = Booking.objects.filter(homestay=h, num_people__gt=0).aggregate(total=Sum('num_people'))['total'] or 0
            user_list.append({
                'homestayName': h.name,
                'ownerName': h.owner.name,
                'address': h.address,
                'username': h.owner.username,
                'status': 'Active' if h.owner.is_active else 'Inactive',
                'totalGuests': total_guests
            })
        # Also include MTO staff and admin accounts for superuser view
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            mto_accounts = []
            # include staff and superusers
            mto_qs = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).order_by('username')
            for u in mto_qs:
                mto_accounts.append({
                    'username': u.username,
                    'name': getattr(u, 'name', '') or (u.get_full_name() if hasattr(u, 'get_full_name') else ''),
                    'email': getattr(u, 'email', '') if hasattr(u, 'email') else '',
                    'role': 'Superuser' if u.is_superuser else 'Staff',
                    'status': 'Active' if u.is_active else 'Inactive'
                })
        except Exception:
            mto_accounts = []

        return JsonResponse({'success': True, 'users': user_list, 'mto_accounts': mto_accounts})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# Server-side search for homestays/users
@require_GET
def api_homestay_search(request):
    """Search homestays by homestay name or owner name. Use ?q=..."""
    q = (request.GET.get('q') or '').strip()
    homestays = Homestay.objects.select_related('owner').all()
    if q:
        homestays = homestays.filter(Q(name__icontains=q) | Q(owner__name__icontains=q) | Q(owner__username__icontains=q))
    from django.db.models import Sum
    user_list = []
    for h in homestays:
        total_guests = Booking.objects.filter(homestay=h, num_people__gt=0).aggregate(total=Sum('num_people'))['total'] or 0
        user_list.append({
            'homestayName': h.name,
            'ownerName': h.owner.name if h.owner else '',
            'address': h.address,
            'username': h.owner.username if h.owner else '',
            'status': 'Active' if h.owner and h.owner.is_active else 'Inactive',
            'totalGuests': total_guests
        })
    return JsonResponse({'success': True, 'users': user_list})


# API endpoint to add a new homestay user (admin creates homestay account)
@csrf_exempt
@require_POST
def add_homestay_user_api(request):
    import sys
    try:
        data = json.loads(request.body.decode('utf-8'))
        username = (data.get('username') or '').strip()
        password = (data.get('password') or '').strip()
        homestay_name = (data.get('homestayName') or '').strip()
        owner_name = (data.get('ownerName') or '').strip()
        address = (data.get('address') or '').strip()
        status = (data.get('status') or 'Active').strip()
        # Validate required fields
        if not username or not password or not homestay_name or not owner_name or not address:
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        # Check username uniqueness and suggest if needed
        orig_username = username
        if CustomUser.objects.filter(username=username).exists():
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=f"{base_username}{counter}").exists():
                counter += 1
            suggested_username = f"{base_username}{counter}"
            return JsonResponse({
                'success': False,
                'error': 'Username already exists.',
                'suggested_username': suggested_username
            }, status=409)
        # Create user with all required fields
        try:
            user = CustomUser.objects.create_user(username=username, password=password, name=owner_name, is_active=(status=='Active'))
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Failed to create user: {str(e)}'}, status=500)
        # Create homestay
        try:
            homestay = Homestay.objects.create(owner=user, name=homestay_name, address=address)
        except Exception as e:
            user.delete()
            return JsonResponse({'success': False, 'error': f'Failed to create homestay: {str(e)}'}, status=500)
        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'homestay_id': homestay.id,
            'username': user.username,
            'homestayName': homestay.name,
            'ownerName': user.name,
            'address': homestay.address,
            'status': 'Active' if user.is_active else 'Inactive'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'General error: {str(e)}'}, status=500)



# API endpoint to get all rooms for the current homestay owner
@csrf_exempt
@require_GET
def room_list_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        homestay = Homestay.objects.get(owner=request.user)
        rooms = Room.objects.filter(homestay=homestay)
        room_list = [
            {
                'id': room.id,
                'room_number': room.room_number,
                'capacity': room.capacity,
                'status': 'Under Maintenance' if room.is_under_maintenance else 'Not Under Maintenance'
            }
            for room in rooms
        ]
        return JsonResponse({'success': True, 'rooms': room_list})
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# API endpoint for adding a new room via AJAX
@csrf_exempt
@require_POST
def room_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        room_number = data.get('room_number')
        capacity = data.get('capacity')
        # Accept both 'status' (from frontend) and 'is_under_maintenance' (legacy)
        status = data.get('status')
        if status is not None:
            is_under_maintenance = (status == 'maintenance')
        else:
            is_under_maintenance = data.get('is_under_maintenance', False)
        if not room_number or not capacity:
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        homestay = Homestay.objects.get(owner=request.user)
        room = Room.objects.create(
            homestay=homestay,
            room_number=room_number,
            capacity=capacity,
            is_under_maintenance=is_under_maintenance
        )
        # Return the full room object for instant dashboard update
        return JsonResponse({
            'success': True,
            'room': {
                'id': room.id,
                'room_number': room.room_number,
                'capacity': room.capacity,
                'status': 'maintenance' if room.is_under_maintenance else 'not_maintenance'
            }
        })
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from datetime import datetime, timedelta
from .models import Homestay, Room, Booking  # Import your models


def home_view(request):
    """
    Render the home page with only registered homestays (with user accounts).
    """
    import json
    homestays = Homestay.objects.filter(owner__isnull=False, owner__is_active=True)
    # Build a dict: {homestay_id: {date: [ {room_number, status}, ... ] } }
    homestay_bookings = {}
    homestay_features = {}
    homestay_dynamic_features = {}
    for homestay in homestays:
        rooms = homestay.rooms.all()
        bookings = homestay.bookings.all()
        # Build a mapping: date -> list of rooms with their statuses
        date_room_status = {}
        # Get all unique dates from bookings
        all_dates = set(b.date for b in bookings)
        for date in all_dates:
            date_str = date.strftime('%Y-%m-%d')
            date_room_status[date_str] = []
            for room in rooms:
                # Find booking for this room and date
                booking = bookings.filter(room=room, date=date).first()
                if booking:
                    status = booking.status
                elif room.is_under_maintenance:
                    status = 'maintenance'
                else:
                    status = 'available'
                date_room_status[date_str].append({
                    'room_number': room.room_number,
                    'status': status
                })
        # Also add all rooms as available for dates in the current month with no bookings
        from datetime import date as dt_date, timedelta
        import calendar
        today = dt_date.today()
        for month_offset in range(0, 2):  # current and next month
            month = (today.month + month_offset - 1) % 12 + 1
            year = today.year + ((today.month + month_offset - 1) // 12)
            days_in_month = calendar.monthrange(year, month)[1]
            for day in range(1, days_in_month + 1):
                d = dt_date(year, month, day)
                date_str = d.strftime('%Y-%m-%d')
                if date_str not in date_room_status:
                    date_room_status[date_str] = []
                    for room in rooms:
                        status = 'maintenance' if room.is_under_maintenance else 'available'
                        date_room_status[date_str].append({
                            'room_number': room.room_number,
                            'status': status
                        })
            homestay_bookings[homestay.id] = date_room_status
            homestay_features[homestay.id] = {
            'max_guests': homestay.max_guests,
            'wifi_available': homestay.wifi_available,
            'videoke_available': homestay.videoke_available,
            'pet_friendly': homestay.pet_friendly,
            'beach_front': homestay.beach_front,
        }
        # Add dynamic features
        homestay_dynamic_features[homestay.id] = list(homestay.features.values('id', 'name', 'type', 'value'))

    # --- Homestay Performance Rankings ---
    from django.db.models import Sum, Count
    from django.db.models import Case, When, IntegerField
    rankings = (
        Homestay.objects.filter(owner__isnull=False, owner__is_active=True)
        .annotate(
            total_arrivals=Sum(
                Case(
                    When(bookings__source='registration', then='bookings__num_people'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )
        .order_by('-total_arrivals')
    )
    # If num_people is null, fallback to count of bookings with source='registration'
    for h in rankings:
        if h.total_arrivals is None:
            h.total_arrivals = h.bookings.filter(source='registration').count()

    bookings_json = json.dumps(homestay_bookings)
    features_json = json.dumps(homestay_features)
    dynamic_features_json = json.dumps(homestay_dynamic_features)
    return render(request, 'tourism/home.html', {
        'homestays': homestays,
        'bookings_json': bookings_json,
        'features_json': features_json,
        'dynamic_features_json': dynamic_features_json,
        'homestay_rankings': rankings,
    })


def get_home_context(request):
    """Build and return the context dict used by the home page.
    This duplicates the data assembly in home_view so other views can render
    the full page (for example, after a failed login) without losing content.
    """
    import json
    homestays = Homestay.objects.filter(owner__isnull=False, owner__is_active=True)
    homestay_bookings = {}
    homestay_features = {}
    homestay_dynamic_features = {}
    for homestay in homestays:
        rooms = homestay.rooms.all()
        bookings = homestay.bookings.all()
        date_room_status = {}
        all_dates = set(b.date for b in bookings)
        from datetime import date as dt_date, timedelta
        import calendar
        for date in all_dates:
            date_str = date.strftime('%Y-%m-%d')
            date_room_status[date_str] = []
            for room in rooms:
                booking = bookings.filter(room=room, date=date).first()
                if booking:
                    status = booking.status
                elif room.is_under_maintenance:
                    status = 'maintenance'
                else:
                    status = 'available'
                date_room_status[date_str].append({'room_number': room.room_number, 'status': status})
        today = dt_date.today()
        for month_offset in range(0, 2):
            month = (today.month + month_offset - 1) % 12 + 1
            year = today.year + ((today.month + month_offset - 1) // 12)
            days_in_month = calendar.monthrange(year, month)[1]
            for day in range(1, days_in_month + 1):
                d = dt_date(year, month, day)
                date_str = d.strftime('%Y-%m-%d')
                if date_str not in date_room_status:
                    date_room_status[date_str] = []
                    for room in rooms:
                        status = 'maintenance' if room.is_under_maintenance else 'available'
                        date_room_status[date_str].append({'room_number': room.room_number, 'status': status})
        homestay_bookings[homestay.id] = date_room_status
        homestay_features[homestay.id] = {
            'max_guests': homestay.max_guests,
            'wifi_available': homestay.wifi_available,
            'videoke_available': homestay.videoke_available,
            'pet_friendly': homestay.pet_friendly,
            'beach_front': homestay.beach_front,
        }
        homestay_dynamic_features[homestay.id] = list(homestay.features.values('id', 'name', 'type', 'value'))

    # Rankings
    from django.db.models import Sum, Case, When, IntegerField
    rankings = (
        Homestay.objects.filter(owner__isnull=False, owner__is_active=True)
        .annotate(
            total_arrivals=Sum(
                Case(
                    When(bookings__source='registration', then='bookings__num_people'),
                    default=0,
                    output_field=IntegerField()
                )
            )
        )
        .order_by('-total_arrivals')
    )
    for h in rankings:
        if h.total_arrivals is None:
            h.total_arrivals = h.bookings.filter(source='registration').count()

    return {
        'homestays': homestays,
        'bookings_json': json.dumps(homestay_bookings),
        'features_json': json.dumps(homestay_features),
        'dynamic_features_json': json.dumps(homestay_dynamic_features),
        'homestay_rankings': rankings,
        # PRG flags for login modal (if present in session)
        'login_error': request.session.pop('login_error', False),
        'login_username': request.session.pop('login_username', ''),
        'login_locked': request.session.pop('login_locked', False),
        'failed_login_attempts': request.session.pop('failed_login_attempts', 0),
    }


@csrf_exempt
def login_view(request):
    """
    Handle user login with optional redirect to next URL.
    Redirect staff users to admin dashboard, others to homestay dashboard.
    """
    next_url = request.GET.get('next', '')
    # Read current failed attempts from session (per-session counter)
    failed = int(request.session.get('failed_login_attempts', 0) or 0)
    # Lockout configuration
    LOCK_THRESHOLD = 4
    LOCK_TIMEOUT = 5 * 60  # 5 minutes in seconds

    # We intentionally only apply username-based temporary lockouts (not IP/device-based)

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password')
        user_key = username.lower() if username else 'unknown'
        user_count_key = f'login_count_user:{user_key}'
        user_block_key = f'login_block_user:{user_key}'

        # If username is already locked, show lock message and don't attempt auth
        blocked_user = cache.get(user_block_key)
        if blocked_user:
            # compute remaining time from username-only block-until
            try:
                now = int(time.time())
                user_until = cache.get(f'login_block_until_user:{user_key}')
                rem = 0
                if user_until:
                    rem = max(0, int(user_until) - now)
            except Exception:
                rem = 0

            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'blocked': True, 'remaining': rem, 'message': 'Your account has been temporarily locked. Please contact MTO staff for assistance.'})
            else:
                # Use session flags + redirect to avoid browser resubmit prompts (PRG)
                request.session['login_error'] = True
                request.session['login_username'] = username
                request.session['login_locked'] = True
                request.session['failed_login_attempts'] = failed
                request.session.modified = True
                return redirect('home')

        user = authenticate(request, username=username, password=password)
        print(f"DEBUG: Attempt login for {username}, authenticated: {user is not None}")
        if user is not None:
            # Reset failed attempts on successful login
            request.session['failed_login_attempts'] = 0
            # Clear cache counters/locks for this IP and username and any block-until keys
            try:
                    cache.delete(user_count_key)
                    cache.delete(user_block_key)
                    cache.delete(f'login_block_until_user:{user_key}')
            except Exception:
                pass
            login(request, user)
            print(f"DEBUG: Logged in as {user.username}, is_superuser={user.is_superuser}, is_staff={user.is_staff}")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                print(f"DEBUG: Redirecting to next_url: {next_url}")
                return redirect(next_url)
            # Redirect admin to admin.html, staff to mtoadmin.html, others to homestay.html
            if user.is_superuser:
                print("DEBUG: Redirecting to admin.html")
                return render(request, 'tourism/admin.html')
            elif user.is_staff:
                print("DEBUG: Redirecting to mto-admin")
                return redirect('mto-admin')
            else:
                print("DEBUG: Redirecting to homestay")
                return redirect('homestay')
        else:
            # Increment failed attempts and persist in session
            failed += 1
            request.session['failed_login_attempts'] = failed
            request.session.modified = True
            print(f"DEBUG: Invalid username or password. Failed attempts={failed}")

            # Increment counters in cache for both username and IP (with expiry)
            try:
                # User count
                ucount = cache.get(user_count_key)
                if ucount is None:
                    cache.set(user_count_key, 1, LOCK_TIMEOUT)
                    ucount = 1
                else:
                    try:
                        ucount = int(ucount) + 1
                    except Exception:
                        ucount = 1
                    cache.set(user_count_key, ucount, LOCK_TIMEOUT)

                # If user count reached threshold, set username-based block key and store 'until' timestamp
                locked = False
                now = int(time.time())
                if ucount >= LOCK_THRESHOLD:
                    cache.set(user_block_key, True, LOCK_TIMEOUT)
                    cache.set(f'login_block_until_user:{user_key}', now + LOCK_TIMEOUT, LOCK_TIMEOUT)
                    locked = True
            except Exception as e:
                print(f"DEBUG: cache error: {e}")
                locked = False

            # Return appropriate message
            if locked:
                # If AJAX, respond with blocked info
                if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                    now = int(time.time())
                    user_until = cache.get(f'login_block_until_user:{user_key}')
                    rem = 0
                    try:
                        if user_until:
                            rem = max(rem, int(user_until) - now)
                    except Exception:
                        rem = 0
                    return JsonResponse({'success': False, 'blocked': True, 'remaining': rem, 'message': 'Your account has been temporarily locked. Please contact MTO staff for assistance.'})
                # Set session flags then redirect to home (PRG)
                request.session['login_error'] = True
                request.session['login_username'] = username
                request.session['login_locked'] = True
                request.session['failed_login_attempts'] = failed
                request.session.modified = True
                return redirect('home')
            else:
                # Invalid credentials
                if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'blocked': False, 'message': 'Invalid username or password.'})

                # Add a Django message so the template can display it under the sign-in form
                try:
                    messages.error(request, 'Invalid username or password.')
                except Exception:
                    pass

                request.session['login_error'] = True
                request.session['login_username'] = username
                request.session['login_locked'] = False
                request.session['failed_login_attempts'] = failed
                request.session.modified = True
                return redirect('home')

    # On GET, pass current failed attempts so template can show info if desired
    context = get_home_context(request)
    context.update({'next': next_url, 'failed_login_attempts': failed})
    return render(request, 'tourism/home.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff or u.is_superuser, login_url='/login/')
def admin_view(request):
    """
    Admin dashboard view for staff/admin.
    Renders admin.html for admin, mtoadmin.html for staff.
    """
    if request.user.is_superuser:
        return render(request, 'tourism/admin.html')
    else:
        # Only show homestays whose owner accounts are active (hide suspended accounts)
        homestays = Homestay.objects.filter(owner__is_active=True).order_by('name')
        # Tourist List: only Booking entries created via registration (exclude calendar reservations)
        from .models import Booking
        all_tourists = list(
            Booking.objects.filter(source='registration').order_by('-created_at').values(
                'guest_name', 'contact_number', 'homestay__name', 'date', 'num_people', 'status'
            )
        )
        # Convert date to string for template rendering
        for t in all_tourists:
            if t['date']:
                t['date'] = t['date'].isoformat()
        # Grouped tourists for management (existing logic)
        from collections import defaultdict
        grouped_tourists = []
        for homestay in homestays:
            # Only consider registration-sourced bookings for tourist management/grouping
            bookings = homestay.bookings.filter(source='registration').order_by('guest_name', 'date')
            guest_map = defaultdict(list)
            for b in bookings:
                if b.guest_name:
                    guest_map[b.guest_name].append(b)
            for guest, bks in guest_map.items():
                if bks:
                    check_in = min(b.date for b in bks)
                    check_out = max(b.date for b in bks)
                    grouped_tourists.append({
                        'homestay': homestay.name,
                        'guest_name': guest,
                        'check_in': check_in,
                        'check_out': check_out,
                        'num_people': bks[0].num_people,
                        'status': bks[0].status,
                    })
        show_management = request.GET.get('show') == 'management'
        return render(request, 'tourism/mtoadmin.html', {
            'homestays': homestays,
            'grouped_tourists': grouped_tourists,
            'all_tourists': all_tourists,
            'all_homestays': homestays,
            'show_management': show_management,
        })


@login_required(login_url='/login/')
def homestay_view(request):
    """
    Homestay dashboard view.
    Shows rooms and stats for the logged-in homestay owner.
    """
    print(f"DEBUG: Entered homestay_view for user {request.user.username} (ID: {request.user.id})")
    # Load homestay and rooms for the logged-in homestay owner
    homestay = Homestay.objects.get(owner=request.user)
    rooms = Room.objects.filter(homestay=homestay)

    total_rooms = rooms.count()
    maintenance_rooms = rooms.filter(is_under_maintenance=True).count()

    # Get booking data for calendar and for tourist management table
    # Only include bookings that are not 'reserved' for tourist management
    bookings = Booking.objects.filter(homestay=homestay).exclude(status='reserved').order_by('date')
    # Convert bookings to JSON format for the calendar
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'status': booking.status,
            'guest_name': booking.guest_name or '',
            'num_people': booking.num_people or 1,
            'start': booking.date.strftime('%Y-%m-%d'),
            'end': booking.date.strftime('%Y-%m-%d')
        })
    bookings_json = json.dumps(bookings_data)

    from django.db.models import Sum
    # Show total tourists (registration-sourced only) regardless of status for management/dashboard
    tourist_bookings = Booking.objects.filter(homestay=homestay, source='registration').order_by('-date')
    print("[DEBUG] All bookings for total_tourists:")
    for b in tourist_bookings:
        print(f"  Booking ID: {b.id}, guest_name: {b.guest_name}, num_people: {b.num_people}, status: {b.status}")
    total_tourists = tourist_bookings.aggregate(total=Sum('num_people'))['total'] or 0
    print(f"[DEBUG] Computed total_tourists: {total_tourists}")
    context = {
        'homestay': homestay,
        'rooms': rooms,
        'total_rooms': total_rooms,
        'maintenance_rooms': maintenance_rooms,
        'bookings_json': bookings_json,
        'bookings': bookings,  # <-- Pass bookings queryset for template
        'total_tourists': total_tourists,
        # Pass new features for dynamic form population
        'max_guests': homestay.max_guests,
        'wifi_available': homestay.wifi_available,
        'videoke_available': homestay.videoke_available,
        'pet_friendly': homestay.pet_friendly,
        'beach_front': homestay.beach_front,
    # 'room_form': room_form,  # removed, not needed for manual room management
    }
    print("[DEBUG] Bookings passed to template:", bookings)
    print("[DEBUG] Total tourists:", total_tourists)
    return render(request, 'tourism/homestay.html', context)


@login_required(login_url='/login/')
@require_GET
def export_tourists_csv(request):
    """
    Export registration-sourced bookings for the logged-in homestay owner as CSV.
    Columns: guest_name, contact_number, homestay_name, date, num_people, status
    """
    try:
        homestay = Homestay.objects.get(owner=request.user)
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)

    bookings = Booking.objects.filter(homestay=homestay, source='registration').order_by('-date')

    # Create the HttpResponse with CSV header
    response = HttpResponse(content_type='text/csv')
    filename = f"tourists_{homestay.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['guest_name', 'contact_number', 'homestay_name', 'date', 'num_people', 'status'])
    for b in bookings:
        writer.writerow([
            b.guest_name or '',
            b.contact_number or '',
            homestay.name or '',
            b.date.isoformat() if b.date else '',
            b.num_people or '',
            b.status or '',
        ])

    return response


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_staff or u.is_superuser, login_url='/login/')
@require_GET
def export_tourists_all_csv(request):
    """
    Staff-only: export all registration-sourced bookings as CSV.
    Optional query params: homestay_id or homestay_name to filter.
    """
    try:
        qs = Booking.objects.filter(source='registration').order_by('-date')
        hid = request.GET.get('homestay_id')
        hname = request.GET.get('homestay_name')
        if hid:
            qs = qs.filter(homestay_id=hid)
        elif hname:
            qs = qs.filter(homestay__name__icontains=hname)

        response = HttpResponse(content_type='text/csv')
        filename = f"tourists_all_{datetime.now().strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        writer = csv.writer(response)
        writer.writerow(['guest_name', 'contact_number', 'homestay_name', 'date', 'num_people', 'status'])
        for b in qs:
            writer.writerow([
                b.guest_name or '',
                b.contact_number or '',
                b.homestay.name if b.homestay else '',
                b.date.isoformat() if b.date else '',
                b.num_people or '',
                b.status or '',
            ])
        return response
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def logout_view(request):
    """
    Log out the current user and redirect to home page.
    """
    logout(request)
    return redirect('home')


@login_required(login_url='/login/')
@require_POST
def change_password_api(request):
    """
    Change the logged-in user's password. Expects JSON: { current_password, new_password }
    Returns JSON success/failure.
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        current = data.get('current_password', '')
        newpw = data.get('new_password', '')
        if not current or not newpw:
            return JsonResponse({'success': False, 'error': 'Missing fields.'}, status=400)
        user = request.user
        # Check current password
        if not user.check_password(current):
            return JsonResponse({'success': False, 'error': 'Current password is incorrect.'}, status=403)
        # Basic length validation
        if len(newpw) < 8:
            return JsonResponse({'success': False, 'error': 'New password must be at least 8 characters.'}, status=400)
        user.set_password(newpw)
        user.save()
        # If the user changed their own password while logged in, re-authentication is optional here.
        return JsonResponse({'success': True, 'message': 'Password changed successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# API endpoint for booking calendar AJAX (create/update booking)
@csrf_exempt
@require_POST
def booking_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
        date_str = data.get('date')
        status = data.get('status')
        guest_name = data.get('guest_name', '')
        num_people = data.get('num_people', 1)
        room_id = data.get('room_id')
        if not date_str or not status:
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        homestay = Homestay.objects.get(owner=request.user)
        room = None
        if room_id:
            try:
                room = Room.objects.get(id=room_id, homestay=homestay)
            except Room.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Room not found.'}, status=404)
        # Update or create booking
        booking, created = Booking.objects.update_or_create(
            homestay=homestay,
            date=date,
            defaults={
                'status': status,
                'guest_name': guest_name,
                'num_people': num_people,
                'room': room,
                # Mark bookings created/updated through the calendar UI as 'calendar'
                'source': 'calendar'
            }
        )
        return JsonResponse({'success': True, 'created': created, 'booking_id': booking.id})
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def add_homestay_feature(request):
    try:
        data = json.loads(request.body.decode('utf-8'))
        homestay = Homestay.objects.get(owner=request.user)
        name = data.get('featureName')
        type_ = data.get('featureType')
        value = data.get('featureValue', '')
        if not name or not type_:
            return JsonResponse({'success': False, 'error': 'Missing name or type'})
        feature = HomestayFeature.objects.create(homestay=homestay, name=name, type=type_, value=value)
        return JsonResponse({'success': True, 'feature': {
            'id': feature.id,
            'name': feature.name,
            'type': feature.type,
            'value': feature.value
        }})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_GET
def get_homestay_features(request):
    try:
        homestay = Homestay.objects.get(owner=request.user)
        features = HomestayFeature.objects.filter(homestay=homestay).order_by('-created_at')
        features_list = [
            {
                'id': f.id,
                'name': f.name,
                'type': f.type,
                'value': f.value
            } for f in features
        ]
        return JsonResponse({'success': True, 'features': features_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
