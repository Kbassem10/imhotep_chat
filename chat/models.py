from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class User(AbstractUser):
    """
    Base user model for users
    """

    email_verify = models.BooleanField(default=False)
    user_photo_path = models.CharField(max_length=100, default='', null=True, blank=True)
    
    def __str__(self):
        return f"{self.username}"

class ChatRoom(models.Model):
    """
    Represents a chat room, which can be for a direct message or a group chat.
    """
    name = models.CharField(max_length=255, blank=True, null=True, default=None)  # Optional: for group chat names
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chat_rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_group = models.BooleanField(default=False) # To distinguish group chats

    def __str__(self):
        if self.is_group and self.name:
            return self.name
        elif not self.is_group and self.participants.count() == 2:
            return f"Direct Chat {self.id}"
        return f"ChatRoom {self.id}"

    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    """
    Represents a chat message in the system.
    """

    STATUS = (
        ('Seen', 'Seen'),
        ('Delivered', 'Delivered'),
        ('Pending', 'Pending')
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS, default='Pending')

    def __str__(self):
        return f"Message from {self.sender.username} in room {self.room.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['timestamp']