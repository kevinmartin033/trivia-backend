from channels.consumer import AsyncConsumer

class GameConsumer(AsyncConsumer):

    async def websocket_connect(self, event):
        await self.send({
            "type": "websocket.accept"
        })

    async def websocket_receive(self):
        pass
