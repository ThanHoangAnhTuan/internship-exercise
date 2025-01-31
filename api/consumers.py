from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .kafka_producer import send_to_kafka
import json
from django.contrib.auth.models import AnonymousUser

class RequestConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        if isinstance(self.scope['user'], AnonymousUser):
            await self.close(code=401)
        else:
            self.user_group_name = f"user_{self.scope['user'].id}"
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        user_id = self.scope["user"].id
        kafka_data = {
            "user_id": user_id,
            "data": content
        }
        
        send_to_kafka('blood_indicator_topic', json.dumps(kafka_data))

        await self.send_json({
            "status": "processing",
            "message": "Data has been sent to Kafka for processing."
        })

    async def send_response(self, event):
        response = event['response']
        await self.send_json(response)