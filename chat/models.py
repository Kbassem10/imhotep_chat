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

class Friendship(models.Model):
    """
    Represents a friendship between two users
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('blocked', 'Blocked'),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='friendship_requests_sent'
    )
    addressee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='friendship_requests_received'
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('requester', 'addressee')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.requester.username} -> {self.addressee.username} ({self.status})"
    
    @classmethod
    def are_friends(cls, user1, user2):
        """Check if two users are friends"""
        return cls.objects.filter(
            models.Q(requester=user1, addressee=user2, status='accepted') |
            models.Q(requester=user2, addressee=user1, status='accepted')
        ).exists()
    
    @classmethod
    def get_friends(cls, user):
        """Get all friends of a user"""
        friendships = cls.objects.filter(
            models.Q(requester=user, status='accepted') |
            models.Q(addressee=user, status='accepted')
        )
        
        friends = []
        for friendship in friendships:
            if friendship.requester == user:
                friends.append(friendship.addressee)
            else:
                friends.append(friendship.requester)
        
        return friends
    
    @classmethod
    def get_pending_requests(cls, user):
        """Get pending friend requests for a user"""
        return cls.objects.filter(addressee=user, status='pending')
    
    @classmethod
    def get_sent_requests(cls, user):
        """Get friend requests sent by a user"""
        return cls.objects.filter(requester=user, status='pending')

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

    @classmethod
    def get_or_create_direct_chat(cls, user1, user2):
        """Get existing direct chat or create new one between two users"""
        # Check if chat room already exists
        existing_room = cls.objects.filter(
            participants=user1,
            is_group=False
        ).filter(
            participants=user2
        ).first()

        if existing_room:
            return existing_room, False

        # Create new chat room
        chat_room = cls.objects.create(is_group=False)
        chat_room.participants.add(user1, user2)
        return chat_room, True

    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    """
    Represents a chat message in the system.
    """

    STATUS = (
        ('Pending', 'Pending'),
        ('Delivered', 'Delivered'),
        ('Seen', 'Seen')
    )

    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS, default='Pending')
    delivered_at = models.DateTimeField(null=True, blank=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    seen_by = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='seen_messages', blank=True)

    def __str__(self):
        return f"Message from {self.sender.username} in room {self.room.id} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        ordering = ['timestamp']

class RoomPresence(models.Model):
    """
    Tracks which users are currently active in which rooms
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    is_online = models.BooleanField(default=True)
    last_seen = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'room')