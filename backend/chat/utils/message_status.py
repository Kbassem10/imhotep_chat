from django.utils import timezone
from ..models import Message, RoomPresence, ChatRoom, User

def update_message_status_to_delivered(message_id):
    """Update message status to delivered when saved to database"""
    try:
        message = Message.objects.get(id=message_id)
        if message.status == 'Pending':
            message.status = 'Delivered'
            message.delivered_at = timezone.now()
            message.save()
            return True
    except Message.DoesNotExist:
        pass
    return False

def mark_messages_as_seen(room_id, user_id):
    """Mark all delivered messages in a room as seen by a specific user"""
    try:
        room = ChatRoom.objects.get(id=room_id)
        user = User.objects.get(id=user_id)
        
        # Get all delivered messages in the room that the user hasn't seen
        messages_to_mark = Message.objects.filter(
            room=room,
            status='Delivered'
        ).exclude(sender=user).exclude(seen_by=user)
        
        seen_message_ids = []
        for message in messages_to_mark:
            message.status = 'Seen'
            message.seen_at = timezone.now()
            message.seen_by.add(user)
            message.save()
            seen_message_ids.append(message.id)
            
        return seen_message_ids
    except (ChatRoom.DoesNotExist, User.DoesNotExist):
        return []

def update_user_presence(user_id, room_id, is_online=True):
    """Update user presence in a room"""
    try:
        room = ChatRoom.objects.get(id=room_id)
        user = User.objects.get(id=user_id)
        
        presence, created = RoomPresence.objects.get_or_create(
            user=user,
            room=room,
            defaults={'is_online': is_online}
        )
        
        if not created:
            presence.is_online = is_online
            presence.last_seen = timezone.now()
            presence.save()
            
        return presence
    except (ChatRoom.DoesNotExist, User.DoesNotExist):
        return None

def get_online_users_in_room(room_id):
    """Get list of users currently online in a room"""
    try:
        room = ChatRoom.objects.get(id=room_id)
        online_users = RoomPresence.objects.filter(
            room=room,
            is_online=True
        ).select_related('user').values_list('user__username', flat=True)
        
        return list(online_users)
    except ChatRoom.DoesNotExist:
        return []
