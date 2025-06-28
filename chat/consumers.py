from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import json
from datetime import datetime
from .models import Message, ChatRoom, User
from .utils.message_status import update_message_status_to_delivered, mark_messages_as_seen, update_user_presence, get_online_users_in_room

class ChatConsumer(AsyncWebsocketConsumer):
    # This method is called when a WebSocket connection is established.
    async def connect(self):
        # Extract the room name from the URL route parameters.
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        # Create a unique group name for the room (used for broadcasting messages).
        self.room_group_name = f'chat_{self.room_id}'
        
        # Get the user from the scope (requires authentication middleware)
        self.user = self.scope.get('user')
        
        # Only allow authenticated users
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Add the current WebSocket connection to the room group.
        await self.channel_layer.group_add(
            self.room_group_name,  # Group name
            self.channel_name      # Channel name (unique for each WebSocket connection)
        )
        # Accept the WebSocket connection.
        await self.accept()
        
        # Notify room that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'username': self.user.username,
                'timestamp': datetime.now().isoformat()
            }
        )

        # Update user presence when they connect
        await self.update_user_presence_db(True)
        
        # Mark messages as seen when user opens the room
        seen_message_ids = await self.mark_room_messages_as_seen()
        if seen_message_ids:
            # Notify other users that messages were seen
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_seen',
                    'seen_message_ids': seen_message_ids,
                    'seen_by': self.user.username
                }
            )

    # This method is called when the WebSocket connection is closed.
    async def disconnect(self, close_code):
        # Update user presence when they disconnect
        if hasattr(self, 'user') and self.user.is_authenticated:
            await self.update_user_presence_db(False)
            
            # Notify room that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'username': self.user.username,
                    'timestamp': datetime.now().isoformat()
                }
            )
        
        # Remove the WebSocket connection from the room group.
        await self.channel_layer.group_discard(
            self.room_group_name,  # Group name
            self.channel_name      # Channel name
        )

    # This method is called when a message is received from the WebSocket.
    async def receive(self, text_data):
        try:
            # Parse the JSON data received from the WebSocket.
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'message')
            
            if message_type == 'message':
                message = text_data_json.get('message', '').strip()
                
                if not message:
                    return
                
                # Save message to database with 'Pending' status
                saved_message = await self.save_message(message)
                
                if saved_message:
                    # Update status to 'Delivered' after successful save
                    await self.update_message_to_delivered(saved_message.id)
                    
                    # Broadcast the message to all WebSocket connections in the room group
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'username': self.user.username,
                            'message_id': saved_message.id,
                            'timestamp': datetime.now().isoformat(),
                            'status': 'Delivered'
                        }
                    )
            
            elif message_type == 'mark_seen':
                # Handle explicit mark as seen requests
                seen_message_ids = await self.mark_room_messages_as_seen()
                if seen_message_ids:
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'messages_seen',
                            'seen_message_ids': seen_message_ids,
                            'seen_by': self.user.username
                        }
                    )
            
            elif message_type == 'typing':
                # Handle typing indicators
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'typing_indicator',
                        'username': self.user.username,
                        'is_typing': text_data_json.get('is_typing', False)
                    }
                )
                
        except json.JSONDecodeError:
            # Handle invalid JSON
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid message format'
            }))

    # This method is called when a message is sent to the room group.
    async def chat_message(self, event):
        # Don't send the message back to the sender
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'message',
                'message': event['message'],
                'username': event['username'],
                'timestamp': event['timestamp']
            }))

    # Handle user joined notifications
    async def user_joined(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'username': event['username'],
                'timestamp': event['timestamp']
            }))

    # Handle user left notifications
    async def user_left(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'username': event['username'],
                'timestamp': event['timestamp']
            }))

    # Handle typing indicators
    async def typing_indicator(self, event):
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    # Handle messages seen notifications
    async def messages_seen(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_seen',
            'seen_message_ids': event['seen_message_ids'],
            'seen_by': event['seen_by']
        }))

    # Update message status to delivered
    @database_sync_to_async
    def update_message_to_delivered(self, message_id):
        return update_message_status_to_delivered(message_id)

    # Mark messages as seen
    @database_sync_to_async
    def mark_room_messages_as_seen(self):
        return mark_messages_as_seen(self.room_id, self.user.id)

    # Update user presence
    @database_sync_to_async
    def update_user_presence_db(self, is_online):
        return update_user_presence(self.user.id, self.room_id, is_online)

    # Save message to database
    @database_sync_to_async
    def save_message(self, message_content):
        try:
            # Get the chat room by ID
            room = ChatRoom.objects.get(id=self.room_id)
            
            message = Message.objects.create(
                sender=self.user,
                room=room,
                content=message_content,
                status='Pending'
            )
            return message
        except ChatRoom.DoesNotExist:
            # Handle case where room doesn't exist
            return None
        except Exception as e:
            # Handle other potential errors
            return None
