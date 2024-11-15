
from channels.generic.websocket import AsyncWebsocketConsumer

class Accounts(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name='accountData'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        print(self.channel_name)

    async def disconnect(self,close_code):
        pass

    async def receive(self,text_data):
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type':'randomFunction',
                'value':text_data,
            }
        )

    async def randomFunction(self,event):
        print (event['value'])
        await self.send(event['value'])
