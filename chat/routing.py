from django.urls import re_path

# from . import consumers # You will create consumers.py later

websocket_urlpatterns = [
    # re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
