from channels.consumer import AsyncConsumer
from django.core.cache import caches
import random
class GameConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        game_num = random.randint(1,3)
        cache = caches['default']
        val = cache.get(str(game_num))
        val = val + 1 if val else 1
        cache.set(str(game_num), val)
        await self.channel_layer.group_add(
            str(game_num),
            self.channel_name
        )
        await self.send({
            "type": "websocket.accept"
        })
        
    async def chat_hi(self, message):
        await self.send({
            "type": "websocket.send",
            "text": message["text"]
        })

    async def websocket_receive(self, event):
        for x in range(1,4):
            val = caches['default'].get(str(x))
            print(x, val)
            await self.channel_layer.group_send(
                str(x),
                {
                    "type": "chat.hi",
                    "text": f"Hi Folks: {val}"
                }
            )

    async def websocket_disconnect(self, event):
        pass