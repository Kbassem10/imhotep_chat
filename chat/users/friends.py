from django.shortcuts import render, redirect
from ..models import User, Friendship, ChatRoom, Message
from django.contrib.auth.decorators import login_required
from ..utils.user_info import get_user_photo
from ..utils.get_user_latest_chat_rooms import get_user_latest_chat_rooms
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

@csrf_exempt
@require_http_methods(["POST"])
def search_user(request):
    try:
        data = json.loads(request.body)
        user_name = data.get('name', '')

        if not user_name:
            return JsonResponse({'error': 'Name is required!'}, status=400)

        #get all users matching the search not with the current user
        users = User.objects.filter(
            username__icontains=user_name
        ).exclude(id=request.user.id)

        #get all friendships for the current user
        friendships = Friendship.objects.filter(
            Q(requester=request.user) | Q(addressee=request.user)
        )

        #create a dictionary to store friendship status for each user
        friendship_status = {}
        for friendship in friendships:
            if friendship.requester == request.user:
                friend_id = friendship.addressee.id
            else:
                friend_id = friendship.requester.id
            friendship_status[friend_id] = friendship.status

        # Categorize users by friendship status to sort them
        accepted_friends = []
        pending_friends = []
        blocked_friends = []
        other_users = []

        for user in users:
            #save each user data
            user_data = {
                'id': user.id, 
                'name': user.username, 
                'email': user.email,
                'friendship_status': friendship_status.get(user.id, 'none')
            }
            
            #categorize them to sort them
            status = friendship_status.get(user.id, 'none')
            if status == 'accepted':
                accepted_friends.append(user_data)
            elif status == 'pending':
                pending_friends.append(user_data)
            elif status == 'blocked':
                blocked_friends.append(user_data)
            else:
                other_users.append(user_data)

        #combine all users in the desired order
        users_list = accepted_friends + pending_friends + blocked_friends + other_users

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
    """Get user's friends list with friendship details"""
    try:
        friendships = Friendship.objects.filter(
            Q(requester=request.user) | Q(addressee=request.user),
            status__in=['accepted', 'Blocked']
        )
        
        friends_list = []
        for friendship in friendships:
            # Get the other user (friend)
            friend = friendship.addressee if friendship.requester == request.user else friendship.requester
            friends_list.append({
                'id': friend.id,
                'name': friend.username,
                'email': friend.email,
                'photo_path': getattr(friend, 'user_photo_path', ''),
                'friendship_id': friendship.id,
                'status': friendship.status
            })
        
        return JsonResponse({
            'success': True,
            'friends': friends_list
        }, status=200)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def get_friend_requests(request):
    """Get pending friend requests"""
    pending_requests = Friendship.get_pending_requests(request.user)
    requests_list = []
    
    for req in pending_requests:
        requests_list.append({
            'id': req.id,
            'username': req.requester.username,
            'user_photo_path': getattr(req.requester, 'user_photo_path', ''),
            'created_at': req.created_at.isoformat(),
            'friendship_id': req.id
        })
    
    return JsonResponse({
        'success': True,
        'requests': requests_list,
        'friend_requests': requests_list  # Keep both formats for compatibility
    }, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def decline_friend_request(request):
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
        
        # Delete the friendship request
        requester_name = friendship.requester.username
        friendship.delete()
        
        return JsonResponse({
            'message': f'Friend request from {requester_name} declined',
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def block_friend(request):
    try:
        data = json.loads(request.body)
        friendship_id = data.get('friendship_id')
        
        if not friendship_id:
            return JsonResponse({'error': 'Friendship ID is required'}, status=400)
        
        try:
            friendship = Friendship.objects.get(
                Q(id=friendship_id) & 
                (Q(requester=request.user) | Q(addressee=request.user)),
                status__in=['accepted', 'Blocked']
            )
        except Friendship.DoesNotExist:
            return JsonResponse({'error': 'Friendship not found'}, status=404)
        
        if friendship.status == 'accepted':
            friendship.status = 'Blocked'
            message = 'Friend blocked successfully'
        elif friendship.status == 'Blocked':
            friendship.status = 'accepted'
            message = 'Friend unblocked successfully'
        else:
            return JsonResponse({'error': 'Invalid friendship status'}, status=404)

        friendship.save()
        
        # Get the other user (friend)
        other_user = friendship.addressee if friendship.requester == request.user else friendship.requester
        
        return JsonResponse({
            'message': message,
            'status': friendship.status,
            'friend': {
                'id': other_user.id,
                'name': other_user.username,
                'email': other_user.email
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def remove_friend(request):
    try:
        data = json.loads(request.body)
        friendship_id = data.get('friendship_id')
        
        if not friendship_id:
            return JsonResponse({'error': 'Friendship ID is required'}, status=400)
        
        try:
            friendship = Friendship.objects.get(
                Q(id=friendship_id) & 
                (Q(requester=request.user) | Q(addressee=request.user)),
                status__in=['accepted', 'Blocked']
            )
        except Friendship.DoesNotExist:
            return JsonResponse({'error': 'Friendship not found'}, status=404)
        
        # Get the other user before deleting
        other_user = friendship.addressee if friendship.requester == request.user else friendship.requester
        
        friendship.delete()
        
        return JsonResponse({
            'message': 'Friendship removed successfully',
            'friend': {
                'id': other_user.id,
                'name': other_user.username,
                'email': other_user.email
            }
        }, status=200)
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
