from django.core.cache import caches
from django.http import JsonResponse
import datetime
import uuid

def join_game(request):
    default_cache = caches['default']
    next_game_id = default_cache.get('next_game')
    if next_game_id:
        game_info = default_cache.get(next_game_id)
    if not next_game_id or datetime.datetime.now() >= game_info["start_time"]:
        next_game_id = uuid.uuid4()
        current_players = 0
        next_game = {
            "id": next_game_id,
            "current_players": current_players,
            "status": "Lobby",
            # TODO: celery based events to start the game instead of this
            # If player threshold is not met we don't want people waiting all day
            "start_time": datetime.datetime.now() + datetime.timedelta(seconds=10) 
        }
        default_cache.set(next_game["id"], next_game)

        default_cache.set("next_game", next_game["id"])
    return JsonResponse({"id": next_game_id})