from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Room

@csrf_exempt
@require_POST
def delete_room_api(request):
    import json
    from django.contrib.auth.decorators import login_required
    try:
        data = json.loads(request.body.decode('utf-8'))
        room_id = data.get('room_id')
        if not room_id:
            return JsonResponse({'success': False, 'error': 'Missing room ID.'}, status=400)
        room = Room.objects.get(id=room_id)
        room.delete()
        return JsonResponse({'success': True})
    except Room.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Room not found.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
