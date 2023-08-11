from rest_framework.serializers import ModelSerializer
from rest_framework import serializers
from .models import Room,FriendRequest,Upload
from django.contrib.auth import get_user_model
from rest_framework.validators import UniqueTogetherValidator
import os
# Creator Serializer
# Public View Serializer
# Allowed View Serializer
# Nested View Serializer


class UserSerializer(ModelSerializer):
    class Meta:
        model=get_user_model()
        fields=['username','id']


class RoomSerializerC(ModelSerializer):
    creator=serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    def validate(self,data):
        if self.context['request'].method=="PATCH":
            if "limit" in data:
                if data['limit'] < 1 or data['limit'] > 100:
                    raise serializers.ValidationError("Limit must be between 1 and 100.")
            if "has_password" in data:
                if data["has_password"]==False:
                    data["password"]=""
                if data['has_password']==True:
                    if "password" in data:
                        if data["password"]=="":
                            raise serializers.ValidationError("Incorrect value for the room's password.")
                    else:
                        raise serializers.ValidationError("Password not provided.")
        else:   
            if data['limit'] < 1 or data['limit'] > 100:
                raise serializers.ValidationError("Limit must be between 1 and 100.")
            if "has_password" in data:
                if data["has_password"]==False:
                    data["password"]=""
                if data['has_password']==True:
                    if "password" in data:
                        if data["password"]=="":
                            raise serializers.ValidationError("Incorrect value for the room's password.")
                    else:
                        raise serializers.ValidationError("Password not provided.")
        return data

    class Meta:
        model=Room
        fields='__all__'
        validators=[UniqueTogetherValidator(queryset=Room.objects.all(),fields=['name','creator'])]

class RoomSerializerP(ModelSerializer):
    creator=UserSerializer()
    member_count=serializers.IntegerField(read_only=True)

    class Meta:
        model=Room
        exclude=['bans','admins','invites','members','password']

class RoomSerializerN(ModelSerializer):
    creator=UserSerializer()

    class Meta:
        model=Room
        fields=['id','creator','name']


class UploadSerializerA(ModelSerializer):
    uploader=UserSerializer()
    room=RoomSerializerN()

    def to_representation(self, instance):
        rep= super().to_representation(instance)
        file=os.path.basename(instance.file.name)
        rep['file']=file
        return rep

    class Meta:
        model=Upload
        fields='__all__'

class RoomSerializerA(ModelSerializer):
    creator=UserSerializer()
    member_count=serializers.IntegerField()
    files=UploadSerializerA(read_only=True,many=True)
    admins=UserSerializer(read_only=True,many=True)
    invites=UserSerializer(read_only=True,many=True)
    bans=UserSerializer(read_only=True,many=True)
    members=UserSerializer(read_only=True,many=True)

    class Meta:
        model=Room
        fields='__all__'




class FriendRequestSerializerC(ModelSerializer):
    sender=serializers.HiddenField(default=serializers.CurrentUserDefault())
    
    def validate(self,data):
        if FriendRequest.objects.filter(receiver=data['sender'],sender=data['receiver']).count() > 0:
            raise serializers.ValidationError("Friend request already exists.")
        if data['receiver'] in data['sender'].friends.all():
            raise serializers.ValidationError("Already friends with this user.")
        if data['receiver']==data['sender']:
            raise serializers.ValidationError("Go get a real friend.")
        return data

    class Meta:
        model=FriendRequest
        fields='__all__'
        validators=[UniqueTogetherValidator(queryset=FriendRequest.objects.all(),fields=['sender','receiver'])]

class FriendRequestSerializerA(ModelSerializer):
    sender=UserSerializer()
    receiver=UserSerializer()

    class Meta:
        model=FriendRequest
        fields='__all__'

class UploadSerializerC(ModelSerializer):
    uploader=serializers.HiddenField(default=serializers.CurrentUserDefault())

    dname=serializers.CharField(default='',required=False)

    def to_representation(self, instance):
        rep= super().to_representation(instance)
        file=os.path.basename(instance.file.name)
        rep['file']=file
        return rep

    def validate(self, data):
        if 'dname' not in data:
            data['dname']=data['file'].name
        elif data['dname']=="" or data['dname'] is None:
            data['dname']=data['file'].name
        if 'caption' not in data:
            data['caption']='Availiable for download'
        if Upload.objects.filter(dname=data['dname'],room=data['room']).count() != 0:
            raise serializers.ValidationError("A file with this dname is already uploaded!")
        return data

    class Meta:
        model=Upload
        fields='__all__'



class ModeSerializer(serializers.Serializer):
    mode=serializers.CharField(max_length=50)

    def validate(self,data):
        if data['mode']!='accept' and data['mode']!='decline':
            raise serializers.ValidationError("Incorrect value for mode, allowed values are : 'accept' or 'decline'")
        return data
    
class FriendUserSerializer(ModelSerializer):
    is_online=serializers.BooleanField()
    currently_in=RoomSerializerN(read_only=True,many=True)

    class Meta:
        model=get_user_model()
        fields=['username','id','is_online','currently_in']


class CurrentUserSerializer(ModelSerializer):
    friends=FriendUserSerializer(read_only=True,many=True)
    creator_of=RoomSerializerA(read_only=True,many=True)
    banned_from=RoomSerializerN(read_only=True,many=True)
    admin_of=RoomSerializerA(read_only=True,many=True)
    invited_to=RoomSerializerA(read_only=True,many=True)
    files=UploadSerializerA(read_only=True,many=True)
    fr_sent=FriendRequestSerializerA(read_only=True,many=True)
    fr_received=FriendRequestSerializerA(read_only=True,many=True)

    class Meta:
        model=get_user_model()
        fields=['username','id','friends','creator_of','banned_from','admin_of','invited_to','files','fr_sent','fr_received']