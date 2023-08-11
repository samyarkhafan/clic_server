import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from clic_api.models import Room
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
from django.contrib.auth.models import AnonymousUser
from clic_api.serializers import RoomSerializerA

# error->client error
# room.join->connection confirmation
# room.message->user message
# room.sys-> system message

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.is_authed=False
        self.user=self.scope['user']
        if self.user==AnonymousUser:
            self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"Not authenticated"
                    }))
            self.close(code=4000)
        self.room_code=self.scope['url_route']['kwargs']['room_code']
        try:
            room=Room.objects.get(code=self.room_code)
        except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"Room not found"
                    }))
                self.close(code=4001)
        else:
            query_dict = parse_qs(self.scope["query_string"].decode())
            password=query_dict['password'][0] if 'password' in query_dict else ''
            result=self.user.joinRoom(room,password)
            if result is None:
                self.is_authed=True
                async_to_sync(self.channel_layer.group_add)(self.room_code,self.channel_name)
                self.send(text_data=json.dumps({
                        "type":f"room.join",
                        "text":{"room":RoomSerializerA(room).data,"welcome":f"{room.welcome_text}"}
                    }))
                async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} joined the room!"}
                    }
                )
                async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":self.user,"room":RoomSerializerA(room).data}
                    }
                )
            else:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":result
                    }))
                self.close(code=4002)

    def receive(self, text_data):
        room=Room.objects.get(code=self.room_code)
        text_data_json=json.loads(text_data)
        if text_data_json['type']=='update':
            if self.user==room.creator:
                async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":"","room":RoomSerializerA(room).data}
                    }
                )
            else:
                self.send(text_data=json.dumps({
                    "type":"error",
                    "text":"Only the creator can brodcast updates"
                }))
        elif text_data_json['type']=='chat':
            async_to_sync(self.channel_layer.group_send)(self.room_code,
                {
                    "type":"room.send",
                    "text":{"type":"room.message","text":f"{self.user.username} : {text_data_json['text']}"}
                }
            )
        elif text_data_json['type']=='kick':
            try:
                user=get_user_model().objects.get(username=text_data_json['text'])
            except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"User not found"
                    }))
            else:
                result=self.user.kickUser(room,user)
                if result is None:
                    
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} kicked {user.username}!"}
                    }
                    
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.close",
                        "text":user
                    }
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":user,"room":RoomSerializerA(room).data}
                    }
                )
                else:
                    self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":result
                    }
                ))
        elif text_data_json['type']=='ban':
            try:
                user=get_user_model().objects.get(username=text_data_json['text'])
            except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"User not found"
                    }))
            else:
                result=self.user.banUser(room,user)
                if result is None:
                    
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} banned {user.username}!"}
                    }
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.close",
                        "text":user
                    }
                )
                    
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":user,"room":RoomSerializerA(room).data}
                    }
                )
                else:
                    self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":result
                    }
                ))
        elif text_data_json['type']=='invite':
            try:
                user=get_user_model().objects.get(username=text_data_json['text'])
            except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"User not found"
                    }))
            else:
                result=self.user.inviteUser(room,user)
                if result is None:
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} invited {user} to room!"}
                    }
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":"","room":RoomSerializerA(room).data}
                    }
                )
                else:
                    self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":result
                    }
                ))
        elif text_data_json['type']=='make_admin':
            try:
                user=get_user_model().objects.get(username=text_data_json['text'])
            except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"User not found"
                    }))
            else:
                result=self.user.makeUserAdmin(room,user)
                if result is None:
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} made {user.username} admin!"}
                    }
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":"","room":RoomSerializerA(room).data}
                    }
                )
                else:
                    self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":result
                    }
                ))
        elif text_data_json['type']=='remove_admin':
            try:
                user=get_user_model().objects.get(username=text_data_json['text'])
            except:
                self.send(text_data=json.dumps({
                        "type":"error",
                        "text":"User not found"
                    }))
            else:
                result=self.user.removeUserAdmin(room,user)
                if result is None:
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} removed {user.username} from the room's admins!"}
                    }
                )
                    async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":"","room":RoomSerializerA(room).data}
                    }
                )
                else:
                    self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":result
                    }
                ))
        elif text_data_json['type']=='delete':
            if self.user==room.creator:
                async_to_sync(self.channel_layer.group_send)(self.room_code,{"type":"room.delete"})
                    
    def disconnect(self, close_code):
        room=Room.objects.get(code=self.room_code)
        if self.is_authed==True:
            self.user.dcRoom(room)
            async_to_sync(self.channel_layer.group_discard)(self.room_code,self.channel_name)
            async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.send",
                        "text":{"type":"room.sys","text":f"{self.user.username} got disconnected from the room!"}
                    }
            )
            async_to_sync(self.channel_layer.group_send)(self.room_code,
                    {
                        "type":"room.info",
                        "text":{"user":"","room":RoomSerializerA(room).data}
                    }
                )
    def room_close(self,event):
        user=event['text']
        if self.user==user:
            self.send(
                text_data=json.dumps({
                    "type":"error",
                    "text":"You have been kicked/banned from this room!"
                })
            )
            self.close()      
            
    def room_info(self,event):
        user=event['text']['user']
        if user!="":
            if self.user!=user:
                self.send(text_data=json.dumps({
                    "type":"room.info",
                    "text":event['text']['room']
                }))
        else:
            self.send(text_data=json.dumps({
                    "type":"room.info",
                    "text":event['text']['room']
                }))

    def room_send(self,event):
        type=event['text']['type']
        text=event['text']['text']
        self.send(json.dumps({
            "type":type,
            "text":text
        }))

    def room_delete(self,event):
        self.send(text_data=json.dumps(
                    {
                        "type":"error",
                        "text":f"THIS ROOM HAS BEEN DELETED BY IT'S CREATOR!"
                    }
        ))
            
        self.close()
        
        