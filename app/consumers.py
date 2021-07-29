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
        if not game_info or datetime.datetime.now() >= game_info["start_time"]:
            return await self.send({
                "type": "websocket.close"
            })
        await self.send({
            "type": "websocket.accept"
        })
        # TODO: Validate user should be in this game using jwt
        game_info["current_players"] += 1
        cache.set(game_id, game_info)
        await self.channel_layer.group_add(
            game_id,
            self.channel_name
        )
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
                "question_number": message["question_number"],
                "answers": message["answers"],
                "expiry": message["expiry"]
            })
        })

    async def game_new_winner(self, message):
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "code": "new_winner"
            })
        })

    async def submit_answer(self, game_id, game_info, message):
        cache = caches["default"]
        question = game_info["questions"][game_info["question_index"]]
        if question["id"] != message["question_id"]:
            question_match = [x for x in game_info["questions"] if x["id"] == message["question_id"]]
            if not question_match:
                self.send({
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
                    "correct_answer": question_match["correct_answer"]
                })
            })
            
        if datetime.datetime.now() > question["expiry"]:
            await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "late_answer",
                    "correct_answer": question["correct_answer"]
                })
            })
            await self.channel_layer.group_discard(
                game_id,
                self.channel_name
            )
        elif message["answer"] == question["correct_answer"]:
            if game_info["question_index"] == 9:
                await self.send({
                    "type": "websocket.send",
                    "text": json.dumps({
                        "code": "game_winner"
                    })
                })
                await self.channel_layer.group_send(
                    game_id,
                    {"type": "game.new_winner"}
                )
            else:
                game_info["questions"][game_info["question_index"]]["submitted_answers"][message["answer"]] += 1
                cache.set(game_id, game_info)
                await self.send({
                    "type": "websocket.send",
                    "text": json.dumps({
                        "code": "correct_answer",
                        "correct_answer": question["correct_answer"]
                    })
                })
        else:
            game_info["questions"][game_info["question_index"]]["submitted_answers"][message["answer"]] += 1
            cache.set(game_id, game_info)
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

    async def next_question(self, message):
        cache = caches["default"]
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        game_info = cache.get(game_id)
        question = game_info["questions"][game_info["question_index"]]
        if "question_id" in message and question["id"] != message["question_id"]:
            return await self.send({
                "type": "websocket.send",
                "text": json.dumps({
                    "code": "next_question_started"
                })
            })
        if question.get("expiry") is None:
            game_info["questions"][game_info["question_index"]]["expiry"] =  datetime.datetime.now() + datetime.timedelta(seconds=10)
            game_info["questions"][game_info["question_index"]]["submitted_answers"] = {x:0 for x in ["A", "B", "C", "D"]}
            cache.set(game_id, game_info)
        elif datetime.datetime.now() > question.get("expiry") + datetime.timedelta(seconds=10):
            game_info["question_index"] += 1
            game_info["questions"][game_info["question_index"]]["submitted_answers"] = {x:0 for x in ["A", "B", "C", "D"]}
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
                "question_number": game_info["question_index"] + 1,
                "answers": question["answers"],
                "expiry": (game_info["questions"][game_info["question_index"]]["expiry"] - datetime.datetime.now()).total_seconds()
            }
        )

    def _get_questions(self):
        question_list = []
        with open("./question_db.json") as questions:
            question_dict = json.loads(questions.read())
            keys = random.sample(question_dict.keys(), 10)
            question_list = [question_dict[x] for x in keys]
        return question_list

    async def question_metrics(self, game_id, game_info, message):
        cache = caches["default"]
        question = game_info["questions"][game_info["question_index"]]
        if question["id"] != message["question_id"]:
            # handle it
            pass
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({
                "code": "question_metrics",
                "metrics": question["submitted_answers"],
                "correct_answer": question["correct_answer"],
                "expiry": ((question["expiry"] + datetime.timedelta(seconds=10)) - datetime.datetime.now() ).total_seconds()
            })
        })
    
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
                game_info["questions"] = self._get_questions()
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
            await self.next_question(message)
        if message["code"] == "game.question_metrics":
            await self.question_metrics(game_id, game_info, message)

    async def websocket_disconnect(self, event):
        game_id = self.scope["url_route"]["kwargs"]["game_id"]
        cache = caches["default"]
        game_info = cache.get(game_id)
        if not game_info:
            return
        game_info["current_players"]  -= 1
        cache.set(game_id, game_info)
        await self.channel_layer.group_discard(
            game_id,
            self.channel_name
        )
        await self.channel_layer.group_send(
            game_id,
            {
                "type": "game.players_count",
                "message": game_info["current_players"],
                "start_time": (game_info["start_time"] - datetime.datetime.now()).total_seconds()
            }
        )