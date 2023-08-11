from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from .models import Room,FriendRequest,Upload,User
from .serializers import RoomSerializerP,RoomSerializerC,RoomSerializerA,FriendRequestSerializerA,FriendRequestSerializerC,ModeSerializer,UploadSerializerA,UploadSerializerC
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.http.response import FileResponse,HttpResponseForbidden,HttpResponseNotFound
from django.conf import settings
from rest_framework.authtoken.models import Token
from django.db.models import Q
# Create your views here.

@api_view(["GET"])
def getRoutes(request):
    if request.method=="GET":
        return Response({"rooms/","rooms/<id>/","frequests/","frequests/<id>/","uploads/","uploads/<id>/","auth/"})

@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def rooms(request):
    if request.method=="GET":
        paginator=PageNumberPagination()
        paginator.page_size=10
        serializer=RoomSerializerP(paginator.paginate_queryset(Room.objects.filter(is_private=False).exclude(id__in=request.user.banned_from.all().only("id")).union(Room.objects.filter(Q(id__in=request.user.admin_of.all().only("id")) | Q(id__in=request.user.member_of.all().only("id")))),request),many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method=="POST":
        serializer=RoomSerializerC(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET","PATCH","DELETE"])
@permission_classes([IsAuthenticated])
def room(request,pk):
    try:
        room=Room.objects.get(pk=pk)
    except:
        return Response({"error":"object not found"},status=status.HTTP_404_NOT_FOUND)
    else:
        if request.method=="DELETE":
            if request.user==room.creator:
                room.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error":"Only the creator can delete the room."},status=status.HTTP_403_FORBIDDEN)
        elif request.method=="GET":
            if request.user in room.members.all() or request.user in room.admins.all():
                serializer=RoomSerializerA(room)
                return Response(serializer.data)
            elif room.is_private==False or request.user in room.invites.all():
                serializer=RoomSerializerP(room)
                return Response(serializer.data)
            else:
                return Response({"error":"Private room, members/admins only"},status=status.HTTP_403_FORBIDDEN)
        elif request.method=="PATCH":
            if request.user==room.creator:
                serializer=RoomSerializerC(room,data=request.data,context={"request":request},partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                else:
                    return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error":"Only the creator can edit the room."},status=status.HTTP_403_FORBIDDEN)
            
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def frequests(request):
    if request.method=="GET":
        if 'mode' not in request.query_params:
            mode=''
        else:
            mode=request.query_params['mode']
        if mode=='received':
            serializer=FriendRequestSerializerA(FriendRequest.objects.filter(receiver=request.user),many=True)
            return Response(serializer.data)
        elif mode=='sent':
            serializer=FriendRequestSerializerA(FriendRequest.objects.filter(sender=request.user),many=True)
            return Response(serializer.data)
        else:
            return Response({"error":"Incorrect value for mode."},status=status.HTTP_400_BAD_REQUEST)
    elif request.method=="POST":
        serializer=FriendRequestSerializerC(data=request.data,context={"request":request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def frequest(request,pk):
    try:
        frequest=FriendRequest.objects.get(pk=pk)
    except:
        return Response({"error":"object not found"},status=status.HTTP_404_NOT_FOUND)
    else:
        if request.method=="POST":
            serializer=ModeSerializer(data=request.data)
            if serializer.is_valid():
                mode=serializer.data['mode']
                if mode=='accept':
                    result=request.user.acceptFriendRequest(frequest)
                    if result is None:
                        return Response(status=status.HTTP_204_NO_CONTENT)
                    else:
                        return Response({"error":result},status=status.HTTP_403_FORBIDDEN)
                elif mode=='decline':
                    result=request.user.declineFriendRequest(frequest)
                    if result is None:
                        return Response(status=status.HTTP_204_NO_CONTENT)
                    else:
                        return Response({"error":result},status=status.HTTP_403_FORBIDDEN)
            else:
                return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)    
        elif request.method=="GET":
            if request.user==frequest.sender or request.user==frequest.receiver:
                serializer=FriendRequestSerializerA(frequest)
                return Response(serializer.data)
            else:
                return Response({"error":"This friend request isn't yours."},status=status.HTTP_403_FORBIDDEN)
            
@api_view(["GET","POST"])
@permission_classes([IsAuthenticated])
def uploads(request):
    if request.method=="GET":
        if 'mode' not in request.query_params:
            mode=''
        else:
            mode=request.query_params['mode']
        if mode=='user':
            serializer=UploadSerializerA(Upload.objects.filter(uploader=request.user),many=True)
            return Response(serializer.data)
        elif mode=='room':
            if 'room' in request.query_params:
                if request.query_params['room'].isdigit():
                    try:
                        room=Room.objects.get(pk=request.query_params['room'])
                    except:
                        return Response({"error":"Room not found."},status=status.HTTP_404_NOT_FOUND)
                    else:
                        if request.user in room.members.all():
                            serializer=UploadSerializerA(Upload.objects.filter(room=request.query_params['room'],room__in=request.user.member_of.all()),many=True)
                            return Response(serializer.data)
                        else:
                            return Response({"error":"Not in room."},status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({"error":"Incorrect value for room."},status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error":"Incorrect value for room."},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error":"Incorrect value for mode."},status=status.HTTP_400_BAD_REQUEST)
    elif request.method=="POST":
        serializer=UploadSerializerC(data=request.data,context={"request":request})
        if serializer.is_valid():
            result=request.user.upload(serializer.validated_data['room'])
            if result is None:
                serializer.save()   
                return Response(serializer.data,status=status.HTTP_200_OK)
            else:
                return Response({"error":result},status=status.HTTP_403_FORBIDDEN)
        else:
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
@api_view(["GET","DELETE"])
@permission_classes([IsAuthenticated])
def upload(request,pk):
    try:
        upload=Upload.objects.get(pk=pk)
    except:
        return Response({"error":"object not found"},status=status.HTTP_404_NOT_FOUND)
    else:
        if request.method=="GET":
            if request.user in upload.room.members.all() or request.user==upload.uploader:
                serializer=UploadSerializerA(upload)
                return Response(serializer.data)
            else:
                return Response({"error":"you are not the uploader of this file nor a member of the room it's been uploaded in"},status=status.HTTP_403_FORBIDDEN)
        elif request.method=="DELETE":
            result=request.user.deleteUpload(upload)
            if result is None:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error":result},status=status.HTTP_403_FORBIDDEN)
            

def uploadDownload(request,rname,dname):
    try:
        user=Token.objects.get(key=request.META['HTTP_AUTHORIZATION'][6:]).user
    except:
        return HttpResponseForbidden()
    else:
        try:
            upload=Upload.objects.get(room__name=rname,dname=dname)
        except:
            return HttpResponseNotFound()
        else:
            if user in upload.room.members.all() or user==upload.uploader:
                file=open(f"files/{upload.file.name}","rb")
                return FileResponse(file,as_attachment=True)
            else:
                return HttpResponseForbidden()