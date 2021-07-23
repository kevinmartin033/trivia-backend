import json
import datetime
import uuid
import random
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
    
    async def submit_answer(self, game_id, game_info, message):
        cache = caches["default"]
        question = game_info["questions"][game_info["question_index"]]
        if question["id"] != message["question_id"]:
            question_match = [x for x in game_info["questions"] if x["id"] == message["question_id"]]
            if not question_match:
                self.self({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "unknown_question"
                })
            })
            question_match = question_match[0]
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "late_answer",
                    "correct_answer": question_match["answer"]
                })
            })
        if message["answer"] == question["correct_answer"]:
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "correct_answer",
                    "correct_answer": question["correct_answer"],
                    "next_question": ((question["expiry"] + datetime.timedelta(seconds=10)) - datetime.datetime.now()).total_seconds()
                })
            })
        else:
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "incorrect_answer",
                    "correct_answer": question["correct_answer"]
                })
            })
            await self.channel_layer.group_discard(
                game_id,
                self.channel_name
            )

    async def next_question(self, event):
        cache = caches["default"]
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        game_info = cache.get(game_id)
        question = game_info["questions"][game_info["question_index"]]
        if question.get("expiry") is None:
            game_info["questions"][game_info["question_index"]]["expiry"] =  datetime.datetime.now() + datetime.timedelta(seconds=12)
            cache.set(game_id, game_info)
        elif datetime.datetime.now() > question.get("expiry") + datetime.timedelta(seconds=10):
            game_info["question_index"] += 1
            game_info["questions"][game_info["question_index"]]["expiry"] = datetime.datetime.now() + datetime.timedelta(seconds=12)
            cache.set(game_id, game_info)
            question = game_info["questions"][game_info["question_index"]]


        cache.set(game_id, game_info)
        await self.channel_layer.group_send(
            game_id,
            {
                "type": "game.next_question",
                "question_id": question["id"],
                "question_text": question["question"],
                "answers": question["answers"]
            }
        )


    def get_questions(self):
        question_list = []
        with open("./question_db.json") as questions:
            question_dict = json.loads(questions.read())
            keys = random.sample(question_dict.keys(), 10)
            question_list = [question_dict[x] for x in keys]
        return question_list
    


    async def websocket_receive(self, event):
        cache = caches["default"]
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        game_info = cache.get(game_id)
        message = json.loads(event["text"])
        if message["code"] == "game.start":
            ## Lock this piece of code
            if game_info["status"] == "Lobby" and datetime.datetime.now() > game_info["start_time"]:
                game_info["status"] = "In Progress"
                cache.set(game_id, game_info)
                game_info["questions"] = self.get_questions()
                game_info["question_index"] = 0
                cache.set("next_game", None)
                cache.set(game_id, game_info)
                await self.channel_layer.group_send(
                    game_id,
                    {
                        "type": "game.start_game"
                    }
                )
                await self.next_question(event)
        if message["code"] == "game.submit_answer":
            await self.submit_answer(game_id, game_info, message)
        if message["code"] == "game.next_question":
            await self.next_question(event)

    async def websocket_disconnect(self, event):
        pass