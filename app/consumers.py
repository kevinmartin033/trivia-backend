import json
import datetime
import uuid
from channels.consumer import AsyncConsumer
from django.core.cache import caches

class GameConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        cache = caches["default"]
        # TODO: make this transactional?
        game_info = cache.get(game_id)
        if not game_info:
            #TODO: how"d u get here
            pass
        # TODO: Validate user should be in this game using jwt
        game_info["current_players"] += 1
        cache.set(game_id, game_info)
        await self.channel_layer.group_add(
            game_id,
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })
        await self.channel_layer.group_send(
            game_id,
            {
                "type": "game.players_count",
                "message": game_info["current_players"],
                "start_time": (game_info["start_time"] - datetime.datetime.now()).total_seconds()
            }
        )
    async def game_players_count(self, message):
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "code": "player_count",
                "message": message["message"],
                "start_time": message["start_time"]
            })
        })

    async def game_start_game(self, message):
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "code": "start_game"
            })
        })

    async def game_next_question(self, message):
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "code": "next_question",
                "question_id": message["question_id"],
                "question_text": message["question_text"],
                "answers": message["answers"]
            })
        })

    async def next_question(self, event):
        cache = caches["default"]
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        game_info = cache.get(game_id)
        question_id = '720de16d-e6f6-4164-9ee4-4bdd3012e3d4'
        questions = cache.get('questions')
        if questions is None or question_id not in questions:
            question = {
                "question": "Do u want to talk about our lord and saviour Jesus Christ?",
                "answers": {
                    "A": "Sorry pal, no time.",
                    "B": "Yes of course",
                    "C": "No",
                    "D": "Absolutely Not"
                },
                "correct_answer": "B",
                "expiry": datetime.datetime.now() + datetime.timedelta(seconds=12) 
            }
            questions = {
                question_id: question
            }
            cache.set('questions', questions)
        game_info["active_question"] = question_id
        cache.set(game_id, game_info)
        await self.channel_layer.group_send(
            game_id,
            {
                "type": "game.next_question",
                "question_id": question_id,
                "question_text": questions[question_id]["question"],
                "answers": questions[question_id]["answers"]
            }
        )


    async def websocket_receive(self, event):
        cache = caches["default"]
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        game_info = cache.get(game_id)
        message = json.loads(event["text"])
        if message["code"] == "game.start":
            if game_info["status"] == "Lobby" and datetime.datetime.now() > game_info["start_time"]:
                game_info["status"] = "In Progress"
                cache.set("next_game", None)
                cache.set(game_id, game_info)
                await self.channel_layer.group_send(
                    game_id,
                    {
                        "type": "game.start_game"
                    }
                )
                await self.next_question(event)

    async def websocket_disconnect(self, event):
        pass