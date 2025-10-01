from django.contrib.admin.models import LogEntry
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_GET

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
@require_GET
def admin_log_user_entries_api(request):
    """
    API endpoint to get admin log entries related to users (add, change, delete).
    Returns: id, action_time, object_id, object_repr, action_flag, change_message, user_id
    """
    try:
        # Only log entries related to the CustomUser model
        user_logs = LogEntry.objects.filter(content_type__model='customuser').order_by('-action_time')
        log_list = []
        for log in user_logs:
            log_list.append({
                'id': log.id,
                'action_time': log.action_time,
                'object_id': log.object_id,
                'object_repr': log.object_repr,
                'action_flag': log.action_flag,
                'change_message': log.change_message,
                'user_id': log.user_id,
            })
        return JsonResponse({'success': True, 'logs': log_list})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
