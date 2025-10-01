from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.db.models import Sum
from .models import CustomUser, Homestay, Room, Booking
import json
import calendar
import datetime

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
        bookings = Booking.objects.filter(homestay=homestay).order_by('-date')
        print(f"[DEBUG] Homestay for user {request.user.username}: {homestay}")
        print(f"[DEBUG] Bookings found: {bookings.count()}")
        for b in bookings:
            print(f"[DEBUG] Booking: guest={b.guest_name}, contact={b.contact_number}, date={b.date}, num_people={b.num_people}, status={b.status}")
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
        print(f"[DEBUG] No homestay found for user {request.user.username}")
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
        # Find user and homestay
        user = CustomUser.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
        homestay = Homestay.objects.filter(owner=user).first()
        if not homestay:
            return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
        # Update user fields
        user.name = owner_name
        user.is_active = (status == 'Active')
        user.save()
        # Update homestay fields
        homestay.name = homestay_name
        homestay.address = address
        homestay.save()
        return JsonResponse({'success': True, 'message': 'User and homestay updated.'})
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
    monthly = Booking.objects.filter(date__year=year, num_people__gt=0)
    monthly = monthly.values_list('date__month').annotate(total=Sum('num_people'))
    monthly_dict = {calendar.month_abbr[m]: t for m, t in monthly}
    # Fill missing months with 0
    monthly_data = {calendar.month_abbr[m]: monthly_dict.get(calendar.month_abbr[m], 0) for m in range(1, 13)}
    # Yearly aggregation for last N years
    start_year = year - year_range + 1
    yearly = Booking.objects.filter(date__year__gte=start_year, num_people__gt=0)
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
    bookings = Booking.objects.filter(num_people__gt=0).order_by('-created_at').values(
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
        contact_number=contact
    )
    return JsonResponse({'success': True, 'message': 'Tourist registered successfully!'})
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.urls import reverse
from .models import CustomUser, Homestay, Room, Booking
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import json
from datetime import datetime, timedelta

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
                num_people=num_tourist
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
        return JsonResponse({'success': True, 'users': user_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
                'status': room.status
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
        status = data.get('status', 'available')
        if not room_number or not capacity:
            return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        homestay = Homestay.objects.get(owner=request.user)
        room = Room.objects.create(
            homestay=homestay,
            room_number=room_number,
            capacity=capacity,
            status=status
        )
        return JsonResponse({'success': True, 'room_id': room.id})
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
    # Build a dict: {homestay_id: [booked_dates]}
    homestay_bookings = {}
    homestay_features = {}
    for homestay in homestays:
        bookings = homestay.bookings.filter(status='reserved').values_list('date', flat=True)
        homestay_bookings[homestay.id] = [d.strftime('%Y-%m-%d') for d in bookings]
        homestay_features[homestay.id] = {
            'max_guests': homestay.max_guests,
            'wifi_available': homestay.wifi_available,
            'videoke_available': homestay.videoke_available,
            'pet_friendly': homestay.pet_friendly,
            'beach_front': homestay.beach_front,
        }
    bookings_json = json.dumps(homestay_bookings)
    features_json = json.dumps(homestay_features)
    return render(request, 'tourism/home.html', {
        'homestays': homestays,
        'bookings_json': bookings_json,
        'features_json': features_json,
    })


def login_view(request):
    """
    Handle user login with optional redirect to next URL.
    Redirect staff users to admin dashboard, others to homestay dashboard.
    """
    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        print(f"DEBUG: Attempt login for {username}, authenticated: {user is not None}")
        if user is not None:
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
            print("DEBUG: Invalid username or password.")
            messages.error(request, 'Invalid username or password.')
            return render(request, 'tourism/home.html', {'next': next_url, 'login_error': True})
    return render(request, 'tourism/home.html', {'next': next_url})


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
        homestays = Homestay.objects.all().order_by('name')
        # Tourist List: all Booking entries with guest_name (registered tourists)
        from .models import Booking
        all_tourists = list(
            Booking.objects.all().order_by('-created_at').values(
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
            bookings = homestay.bookings.order_by('guest_name', 'date')
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
    try:
        homestay = Homestay.objects.get(owner=request.user)
        print(f"DEBUG: Found homestay for user {request.user.username}")
    except Homestay.DoesNotExist:
        print(f"DEBUG: No homestay found for user {request.user.username} (ID: {request.user.id})")
        messages.error(request, "No homestay found for this user account.")
        logout(request)  # Log out if no homestay is associated
        return redirect('login')

    rooms = homestay.rooms.all().order_by('room_number')

    # Calculate dashboard stats
    total_rooms = rooms.count()
    available_rooms = rooms.filter(status='available').count()
    reserved_rooms = rooms.filter(status='reserved').count()
    occupied_rooms = rooms.filter(status='occupied').count()
    maintenance_rooms = rooms.filter(status='maintenance').count()

    occupancy_rate = 0
    if total_rooms > 0:
        # Occupancy is usually (Occupied + Reserved) / Total
        occupancy_rate = round(((occupied_rooms + reserved_rooms) / total_rooms) * 100)


    # Get booking data for calendar and for tourist management table
    bookings = Booking.objects.filter(homestay=homestay).order_by('date')
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

    context = {
        'homestay': homestay,
        'rooms': rooms,
        'total_rooms': total_rooms,
        'available_rooms': available_rooms,
        'reserved_rooms': reserved_rooms,
        'occupied_rooms': occupied_rooms,
        'maintenance_rooms': maintenance_rooms,
        'occupancy_rate': occupancy_rate,
        'bookings_json': bookings_json,
        'bookings': bookings,  # <-- Pass bookings queryset for template
        # Pass new features for dynamic form population
        'max_guests': homestay.max_guests,
        'wifi_available': homestay.wifi_available,
        'videoke_available': homestay.videoke_available,
        'pet_friendly': homestay.pet_friendly,
        'beach_front': homestay.beach_front,
    }
    print("[DEBUG] Bookings passed to template:", bookings)
    return render(request, 'tourism/homestay.html', context)


def logout_view(request):
    """
    Log out the current user and redirect to home page.
    """
    logout(request)
    return redirect('home')


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
                'room': room
            }
        )
        return JsonResponse({'success': True, 'created': created, 'booking_id': booking.id})
    except Homestay.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homestay not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
