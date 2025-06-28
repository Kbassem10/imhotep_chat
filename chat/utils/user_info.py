from ..models import User
def get_user_photo(user_id):
    try:
        user_photo_path = User.objects.get(id=user_id).user_photo_path
        if user_photo_path:
            return user_photo_path
    except User.DoesNotExist:
        pass
    
    return None