from django.shortcuts import render, redirect
from .models import User, Friendship, ChatRoom, Message
from django.contrib.auth.decorators import login_required
from .utils.user_info import get_user_photo
from .utils.get_user_latest_chat_rooms import get_user_latest_chat_rooms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

#the Main Page route
@login_required
def main(request):
    user_photo_path = get_user_photo(request.user.id)
    user_latest_chat_rooms = get_user_latest_chat_rooms(request.user.id)
    
    context = {
        'user_photo_path': user_photo_path,
        'user_latest_chat_rooms': user_latest_chat_rooms,
        'user': request.user
    }
    
    return render(request, "main_menu.html", context)

@csrf_exempt
@require_http_methods(["POST"])
def search_user(request):
    try:
        data = json.loads(request.body)
        user_name = data.get('name', '')

        if not user_name:
            return JsonResponse({'error': 'Name is required!'}, status=400)

        users = User.objects.filter(username__icontains = user_name)

        users_list = [{'id': user.id, 'name': user.username, 'email':user.email} for user in users]

        return JsonResponse({'users': users_list}, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def add_friend(request):
    try:
        data = json.loads(request.body)
        friend_id = data.get('friend_id')

        if not friend_id:
            return JsonResponse({'error': 'Friend ID is required'}, status=400)
            
        try:
            friend = User.objects.get(id=friend_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User Not Found'}, status=404)

        if request.user == friend:
            return JsonResponse({'error': 'Cannot add your self as a friend'}, status=400)
        
        existing_friendship = Friendship.objects.filter(
            Q(requester=request.user, addressee=friend) |
            Q(requester=friend, addressee=request.user)
        ).first()

        if existing_friendship:
            if existing_friendship.status == 'accepted':
                return JsonResponse({'error': 'Already friends'}, status=400)
            elif existing_friendship.status == 'pending':
                return JsonResponse({'error': 'Friend request already sent'}, status=400)
            elif existing_friendship.status == 'blocked':
                return JsonResponse({'error': 'Cannot send friend request'}, status=400)
        
        # Create friendship request
        friendship = Friendship.objects.create(
            requester=request.user,
            addressee=friend,
            status='pending'
        )

        return JsonResponse({
            'message': 'Friend request sent successfully',
            'friendship_id': friendship.id,
            'friend': {
                'id': friend.id,
                'name': friend.username,
                'email': friend.email
            }
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
@require_http_methods(["POST"])
def accept_friend_request(request):
    try:
        data = json.loads(request.body)
        friendship_id = data.get('friendship_id')
        
        if not friendship_id:
            return JsonResponse({'error': 'Friendship ID is required'}, status=400)
        
        try:
            friendship = Friendship.objects.get(
                id=friendship_id,
                addressee=request.user,
                status='pending'
            )
        except Friendship.DoesNotExist:
            return JsonResponse({'error': 'Friend request not found'}, status=404)
        
        friendship.status = 'accepted'
        friendship.save()
        
        return JsonResponse({
            'message': 'Friend request accepted',
            'friend': {
                'id': friendship.requester.id,
                'name': friendship.requester.username,
                'email': friendship.requester.email
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_friends(request):
    """Get user's friends list"""
    friends = Friendship.get_friends(request.user)
    friends_list = [
        {
            'id': friend.id,
            'name': friend.username,
            'email': friend.email,
            'photo_path': friend.user_photo_path
        }
        for friend in friends
    ]
    
    return JsonResponse({'friends': friends_list}, status=200)

@login_required
def get_friend_requests(request):
    """Get pending friend requests"""
    pending_requests = Friendship.get_pending_requests(request.user)
    requests_list = [
        {
            'id': req.id,
            'requester': {
                'id': req.requester.id,
                'name': req.requester.username,
                'email': req.requester.email
            },
            'created_at': req.created_at.isoformat()
        }
        for req in pending_requests
    ]
    
    return JsonResponse({'friend_requests': requests_list}, status=200)

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
            'chat_room_id': chat_room.id,
            'message': 'Chat room created successfully' if created else 'Chat room already exists'
        }, status=201 if created else 200)

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
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        messages = Message.objects.filter(room=chat_room).order_by('timestamp')
        
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender_id': message.sender.id,
                'sender_name': message.sender.username,
                'timestamp': message.timestamp.isoformat(),
                'status': message.status
            })
        
        return JsonResponse({'messages': messages_data}, status=200)
        
    except ChatRoom.DoesNotExist:
        return JsonResponse({'error': 'Chat room not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)