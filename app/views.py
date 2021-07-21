from django.core.cache import caches
from django.http import JsonResponse
import uuid

def join_game(request):
    default_cache = caches['default']
    next_game = default_cache.get('next_game')
    if not next_game:
        next_game_id = uuid.uuid4()
        current_players = 1
        next_game = {
            'id': next_game_id,
            'current_players': current_players
        }
    else:
        current_players = next_game['current_players'] + 1
        next_game = {
            'id': next_game['id'],
            'current_players': current_players
        }
    default_cache.set('next_game', next_game)
    return JsonResponse({'id': next_game['id']})