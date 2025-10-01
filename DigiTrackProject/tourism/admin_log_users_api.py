from django.contrib.admin.models import LogEntry
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET
from .models import CustomUser, Homestay

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_GET
def admin_log_users_as_users_api(request):
    """
    API endpoint to get users (with user info) that have admin log entries (Add action).
    Returns: id, homestayName, ownerName, address, username, status
    """
    try:
        # Get all user add log entries
        user_logs = LogEntry.objects.filter(content_type__model='customuser', action_flag=1).order_by('-action_time')
        user_ids = [log.object_id for log in user_logs if log.object_id]
        # Remove duplicates, preserve order
        seen = set()
        unique_user_ids = []
        for uid in user_ids:
            if uid not in seen:
                seen.add(uid)
                unique_user_ids.append(uid)
        users = CustomUser.objects.filter(id__in=unique_user_ids)
        user_list = []
        for u in users:
            homestay = Homestay.objects.filter(owner=u).first()
            user_list.append({
                'id': u.id,
                'homestayName': homestay.name if homestay else '',
                'ownerName': u.name,
                'address': homestay.address if homestay else '',
                'username': u.username,
                'status': 'Active' if u.is_active else 'Inactive'
            })
        return JsonResponse({'success': True, 'users': user_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
