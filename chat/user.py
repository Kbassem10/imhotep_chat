from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth.decorators import login_required
from .utils.user_info import get_user_photo
from .utils.get_user_latest_chat_rooms import get_user_latest_chat_rooms

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
