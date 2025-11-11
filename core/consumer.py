import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
import redis
import json
from django.utils import timezone
from .models import *

# Initialize Redis connection (optional - for persistent online status)
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
except:
    r = None

class OnlineStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_authenticated:
            self.user_id = str(self.user.id)
            self.user_group = f"user_{self.user_id}"
            
            # Add user to their personal group and online users group
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.channel_layer.group_add("online_users", self.channel_name)
            
            await self.accept()
            
            # Mark user as online
            await self.update_online_status(True)
            
            # Notify others that this user came online
            await self.channel_layer.group_send(
                "online_users",
                {
                    'type': 'user_online_status',
                    'user_id': self.user_id,
                    'username': self.user.username,
                    'is_online': True
                }
            )
            
    async def disconnect(self, close_code):
        if hasattr(self, 'user') and self.user.is_authenticated:
            # Mark user as offline
            await self.update_online_status(False)
            
            # Notify others that this user went offline
            await self.channel_layer.group_send(
                "online_users",
                {
                    'type': 'user_online_status',
                    'user_id': self.user_id,
                    'username': self.user.username,
                    'is_online': False
                }
            )
            
            # Remove from groups
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
            await self.channel_layer.group_discard("online_users", self.channel_name)
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'heartbeat':
                # Update last activity timestamp
                await self.update_last_activity()
                
        except json.JSONDecodeError:
            pass
    
    async def user_online_status(self, event):
        """Receive online/offline status updates"""
        await self.send(text_data=json.dumps({
            'type': 'user_status_update',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online']
        }))
    
    @sync_to_async
    def update_online_status(self, online):
        """Update user's online status in the database"""
        try:
            # Check what type of user this is and update accordingly
            if hasattr(self.user, 'student'):
                profile = self.user.student
            elif hasattr(self.user, 'teacher'):
                profile = self.user.teacher
            elif hasattr(self.user, 'parent'):
                profile = self.user.parent
            else:
                return  # Regular user without profile
            
            profile.is_online = online
            profile.last_activity = timezone.now()
            profile.save()
            
        except Exception as e:
            print(f"Error updating online status: {e}")
    
    @sync_to_async
    def update_last_activity(self):
        """Update user's last activity timestamp"""
        try:
            if hasattr(self.user, 'student'):
                profile = self.user.student
            elif hasattr(self.user, 'teacher'):
                profile = self.user.teacher
            elif hasattr(self.user, 'parent'):
                profile = self.user.parent
            else:
                return
            
            profile.last_activity = timezone.now()
            profile.save()
            
        except Exception as e:
            print(f"Error updating last activity: {e}")

def check_user_online(user):
    """
    Check if a user is currently online based on their profile type
    """
    try:
        # Determine user type and get their profile
        if hasattr(user, 'student'):
            profile = user.student
        elif hasattr(user, 'teacher'):
            profile = user.teacher
        elif hasattr(user, 'parent'):
            profile = user.parent
        else:
            return False  # Regular user without profile
        
        # Check if user is marked as online
        if profile.is_online:
            return True
        
        # Fallback: Check last activity (within last 5 minutes)
        if hasattr(profile, 'last_activity'):
            time_diff = timezone.now() - profile.last_activity
            return time_diff.total_seconds() < 300  # 5 minutes
        
        return False
        
    except Exception as e:
        print(f"Error checking online status: {e}")
        return False