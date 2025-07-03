from django.shortcuts import render, redirect
from ..models import User, Friendship, ChatRoom, Message
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ..utils.user_info import get_user_photo
from ..utils.get_user_latest_chat_rooms import get_user_latest_chat_rooms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Max
import json

#the Main Page route
@login_required
def main_menu(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get chat rooms where the user is a participant, ordered by latest message
    user_chat_rooms = ChatRoom.objects.filter(
        participants=request.user
    ).prefetch_related(
        'participants', 
        'messages__sender'
    ).annotate(
        latest_message_time=Max('messages__timestamp')
    ).order_by('-latest_message_time')
    
    # Prepare chat room data with other user info and last message
    user_latest_chat_rooms = []
    for chat_room in user_chat_rooms:
        if not chat_room.is_group:
            # For direct chats, get the other participant
            other_users = chat_room.participants.exclude(id=request.user.id)
            if other_users.exists():
                other_user = other_users.first()
                
                # Get the last message
                last_message = chat_room.messages.order_by('-timestamp').first()
                last_message_content = ""
                if last_message:
                    if last_message.sender == request.user:
                        last_message_content = f"You: {last_message.content}"
                    else:
                        last_message_content = last_message.content
                
                # Use username instead of first/last name
                user_latest_chat_rooms.append({
                    'id': chat_room.id,
                    'other_user_name': other_user.username,  # Changed from first_name + last_name
                    'other_user_photo': other_user.user_photo_path if other_user.user_photo_path else None,
                    'last_message': last_message_content,
                    'unread_count': 0  # You can implement unread count logic here
                })
        else:
            # For group chats, use the group name
            last_message = chat_room.messages.order_by('-timestamp').first()
            last_message_content = ""
            if last_message:
                if last_message.sender == request.user:
                    last_message_content = f"You: {last_message.content}"
                else:
                    last_message_content = f"{last_message.sender.username}: {last_message.content}"
            
            user_latest_chat_rooms.append({
                'id': chat_room.id,
                'other_user_name': chat_room.name or f"Group Chat {chat_room.id}",
                'other_user_photo': None,  # Groups don't have photos for now
                'last_message': last_message_content,
                'unread_count': 0
            })
    
    return render(request, 'main_menu.html', {
        'user_latest_chat_rooms': user_latest_chat_rooms
    })

@csrf_exempt
@require_http_methods(["POST"])
def start_chat(request):
    """Start or get existing chat room between two users"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')

        if not user_id:
            return JsonResponse({'error': 'User ID is required'}, status=400)
            
        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        if request.user == other_user:
            return JsonResponse({'error': 'Cannot start chat with yourself'}, status=400)

        # Get or create chat room (removed friendship requirement)
        chat_room, created = ChatRoom.get_or_create_direct_chat(request.user, other_user)

        return JsonResponse({
            'success': True,
            'chat_room_id': chat_room.id,
            'message': 'Chat room created successfully' if created else 'Chat room ready'
        }, status=201 if created else 200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Send a message to a chat room"""
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        content = data.get('message')

        if not room_id or not content:
            return JsonResponse({'error': 'Room ID and message are required'}, status=400)
            
        try:
            chat_room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return JsonResponse({'error': 'Chat room not found'}, status=404)

        # Check if user is a participant
        if not chat_room.participants.filter(id=request.user.id).exists():
            return JsonResponse({'error': 'Access denied'}, status=403)

        # Create the message
        message = Message.objects.create(
            room=chat_room,
            sender=request.user,
            content=content.strip()
        )

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'timestamp': message.timestamp.isoformat()
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_messages(request, chat_room_id):
    """Get messages for a specific chat room"""
    try:
        chat_room = ChatRoom.objects.get(id=chat_room_id)
        
        # Check if user is a participant
        if not chat_room.participants.filter(id=request.user.id).exists():
            return JsonResponse({
                'success': False,
                'error': 'Access denied'
            }, status=403)
        
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'timestamp': message.timestamp.isoformat(),
                'status': getattr(message, 'status', 'sent')
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data
        }, status=200)
        
    except ChatRoom.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Chat room not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
