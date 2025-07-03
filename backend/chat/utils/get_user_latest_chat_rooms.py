from django.db.models import Max
from ..models import User, ChatRoom, Message

def get_user_latest_chat_rooms(user_id):
    if not user_id:
        return []
    
    try:
        user = User.objects.get(id=user_id)
        
        chat_rooms = ChatRoom.objects.filter(
            participants=user
        ).annotate(
            latest_message_time=Max('messages__timestamp')
        ).order_by('-latest_message_time', '-created_at')
        
        # Enhanced chat room data with proper names and latest messages
        enhanced_chat_rooms = []
        for room in chat_rooms:
            # Get the other participant's name for direct chats
            if not room.is_group:
                other_participants = room.participants.exclude(id=user_id)
                if other_participants.exists():
                    room.name = other_participants.first().username
                else:
                    room.name = f"Chat {room.id}"
            
            # Get the latest message
            latest_message = room.messages.order_by('-timestamp').first()
            if latest_message:
                room.last_message = latest_message.content
                room.last_message_time = latest_message.timestamp
            else:
                room.last_message = "No messages yet"
                room.last_message_time = room.created_at
            
            enhanced_chat_rooms.append(room)
        
        return enhanced_chat_rooms
    
    except User.DoesNotExist:
        return []

