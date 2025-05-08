from channels.generic.websocket import AsyncWebsocketConsumer
import json

class ChatConsumer(AsyncWebsocketConsumer):
    # This method is called when a WebSocket connection is established.
    async def connect(self):
        # Extract the room name from the URL route parameters.
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        # Create a unique group name for the room (used for broadcasting messages).
        self.room_group_name = f'chat_{self.room_name}'

        # Add the current WebSocket connection to the room group.
        await self.channel_layer.group_add(
            self.room_group_name,  # Group name
            self.channel_name      # Channel name (unique for each WebSocket connection)
        )
        # Accept the WebSocket connection.
        await self.accept()

    # This method is called when the WebSocket connection is closed.
    async def disconnect(self, close_code):
        # Remove the WebSocket connection from the room group.
        await self.channel_layer.group_discard(
            self.room_group_name,  # Group name
            self.channel_name      # Channel name
        )

    # This method is called when a message is received from the WebSocket.
    async def receive(self, text_data):
        # Parse the JSON data received from the WebSocket.
        text_data_json = json.loads(text_data)
        message = text_data_json['message']  # Extract the message content.

        # Broadcast the message to all WebSocket connections in the room group.
        await self.channel_layer.group_send(
            self.room_group_name,  # Group name
            {
                'type': 'chat_message',  # Event type (used to route the message)
                'message': message       # Message content
            }
        )

    # This method is called when a message is sent to the room group.
    async def chat_message(self, event):
        message = event['message']  # Extract the message content from the event.

        # Send the message to the WebSocket.
        await self.send(text_data=json.dumps({
            'message': message  # Send the message as JSON.
        }))
