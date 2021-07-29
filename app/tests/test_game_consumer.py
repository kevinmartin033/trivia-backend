import os
import datetime
import pytest
import json
import time
from mock import patch
from channels.testing import WebsocketCommunicator
from app.consumers import GameConsumer
from django.core.cache import caches

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.tests.settings')

@pytest.fixture()
def new_game():
    caches["default"].set("abc", {
        "id": "abc",
        "current_players": 0,
        "status": "Lobby",
        "start_time": datetime.datetime.now() + datetime.timedelta(seconds=10) 
    })

@pytest.fixture()
def ready_for_answer():
    return {
        'id': 'abc',
        'current_players': 1,
        'status': 'In Progress',
        'start_time': datetime.datetime(2021, 7, 29, 0, 1, 9, 367522),
        'questions': [
            {
                'question': 'What is 1+1',
                'id': "0",
                'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'},
                'correct_answer': 'B',
                'expiry': datetime.datetime.now() + datetime.timedelta(milliseconds=500),
                'submitted_answers': {'A': 0, 'B': 0, 'C': 0, 'D': 0}},
            {'question': 'What is 2+1', 'id': "1", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'}
        ],
        'question_index': 0
    }

@pytest.fixture()
def ready_for_metrics():
    return {
        'id': 'abc',
        'current_players': 1,
        'status': 'In Progress',
        'start_time': datetime.datetime.now(),
        'questions': [
            {
                'question': 'What is 1+1',
                'id': "0",
                'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'},
                'submitted_answers': {'A': 1, 'B': 30, 'C': 1, 'D': 1},
                'correct_answer': 'B',
                'expiry': datetime.datetime.now() + datetime.timedelta(milliseconds=500)
            },
            {'question': 'What is 2+1', 'id': "1", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'}
        ],
        'question_index': 0
    }


@pytest.fixture()
def ready_to_win():
    return {
        'id': 'abc',
        'current_players': 1,
        'status': 'In Progress',
        'start_time': datetime.datetime.now(),
        'questions': [
            {
                'question': 'What is 1+1',
                'id': "0",
                'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'},
                'submitted_answers': {'A': 1, 'B': 30, 'C': 1, 'D': 1},
                'correct_answer': 'B',
                'expiry': datetime.datetime.now() + datetime.timedelta(milliseconds=500)
            },
            {'question': 'What is 2+1', 'id': "1", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "2", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "3", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "4", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "5", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "6", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "7", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "8", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A'},
            {'question': 'What is 2+1', 'id': "9", 'answers': {'A': '3', 'B': '2', 'C': '5', 'D': '6'}, 'correct_answer': 'A', 'expiry': datetime.datetime.now() + datetime.timedelta(milliseconds=500)}
        ],
        'question_index': 9
    }


@pytest.fixture()
def ready_to_start():
    return {
        "id": "abc",
        "current_players": 0,
        "status": "Lobby",
        "start_time": datetime.datetime.now() + datetime.timedelta(milliseconds=100)
    }

def get_questions(self):
    return [
        {"question": "What is 1+1", "id": "0", "answers": {"A": "3", "B": "2", "C": "5", "D": "6"}, "correct_answer": "B"},
        {"question": "What is 2+1", "id": "1", "answers": {"A": "3", "B": "2", "C": "5", "D": "6"}, "correct_answer": "A"}
    ]

@pytest.mark.asyncio
async def test_connect_valid_game(new_game):
    communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
    try:
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "player_count"
        assert resp["message"] == 1
    finally:
        await communicator.disconnect()


@pytest.mark.asyncio
async def test_connect_invalid_game(new_game):
    communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abcd/")
    try:
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abcd"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == False
    finally:
        await communicator.disconnect()

@patch.object(GameConsumer, "_get_questions", get_questions)
@pytest.mark.asyncio
async def test_game_start(ready_to_start):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        time.sleep(1)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.start"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        actual = caches["default"].get("abc")["questions"]
        excpected =  get_questions(None)
        [x['question'] for x in actual] == [x['question'] for x in excpected]
        [x['answers'] for x in actual] == [x['answers'] for x in excpected]
        [x['correct_answer'] for x in actual] == [x['correct_answer'] for x in excpected]
    finally:
        await communicator.disconnect()


@pytest.mark.asyncio
async def test_submit_correct_answer(ready_to_start, ready_for_answer):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        caches["default"].set("abc", ready_for_answer)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.submit_answer",
            "question_id": "0",
            "answer": "B"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "correct_answer"
        assert resp["correct_answer"] == "B"
    finally:
        await communicator.disconnect()

@pytest.mark.asyncio
async def test_submit_late_answer(ready_to_start, ready_for_answer):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        caches["default"].set("abc", ready_for_answer)
        time.sleep(1)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.submit_answer",
            "question_id": "0",
            "answer": "B"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "late_answer"
        assert resp["correct_answer"] == "B"
    finally:
        await communicator.disconnect()

@pytest.mark.asyncio
async def test_submit_incorrect_answer(ready_to_start, ready_for_answer):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        caches["default"].set("abc", ready_for_answer)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.submit_answer",
            "question_id": "0",
            "answer": "B"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "correct_answer"
        assert resp["correct_answer"] == "B"
    finally:
        await communicator.disconnect()

@pytest.mark.asyncio
async def test_submit_incorrect_answer(ready_to_start, ready_for_metrics):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        caches["default"].set("abc", ready_for_metrics)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.question_metrics",
            "question_id": "0",
            "answer": "B"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "question_metrics"
        assert resp["metrics"] == {'A': 1, 'B': 30, 'C': 1, 'D': 1}
    finally:
        await communicator.disconnect()

@pytest.mark.asyncio
async def test_win_game(ready_to_start, ready_to_win):
    caches["default"].set("abc", ready_to_start)
    try:
        communicator = WebsocketCommunicator(GameConsumer.as_asgi(), "/game/abc/")
        communicator.scope["url_route"] = {
            "kwargs": {
                "game_id": "abc"
            }
        }
        connected, _ = await communicator.connect()
        assert connected == True
        resp = await communicator.receive_from()
        caches["default"].set("abc", ready_to_win)
        await communicator.send_to(text_data=json.dumps({
            "code": "game.submit_answer",
            "question_id": "9",
            "answer": "A"
        }))
        resp = await communicator.receive_from()
        resp = json.loads(resp)
        assert resp["code"] == "game_winner"
    finally:
        await communicator.disconnect()