from django.db.models import Max
from ..models import User, ChatRoom, Message

def get_user_latest_chat_rooms(user_id):
    if not user_id:
        return None
    
    try:
        user = User.objects.get(id=user_id)
        
        chat_rooms = ChatRoom.objects.filter(
            participants=user
        ).annotate(
            latest_message_time=Max('messages__timestamp')
        ).order_by('-latest_message_time', '-created_at')
        
        return list(chat_rooms)
    
    except User.DoesNotExist:
        return None

