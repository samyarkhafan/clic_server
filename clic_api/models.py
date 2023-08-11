from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import datetime
from django.utils.timezone import now

# Create your models here.


class User(AbstractUser):
    friends = models.ManyToManyField("self", blank=True)
    
    @property
    def is_online(self):
        if self.member_of.count() > 0:
            return True
        else:
            return False

    @property
    def currently_in(self):
        return self.member_of.all().filter(is_private=False)


    def acceptFriendRequest(self, frequest: "FriendRequest"):
        if frequest.receiver == self:
            return frequest.accept()
        else:
            return "This friend request is not for you to accept."

    def declineFriendRequest(self, frequest: "FriendRequest"):
        if frequest.receiver == self:
            return frequest.decline()
        else:
            return "This friend request is not for you to decline."

    def upload(self, room: "Room"):
        if self in room.members.all():
            if self == room.creator:
                return None
            elif self in room.admins.all():
                if room.can_admins_upload==True:
                    return None
                else:
                    return "This room won't allow admin uploads."
            else:
                if room.can_upload==True:
                    return None
                else:
                    return "This room won't allow member uploads."
        else:
            return "You need to be in the room to upload a file."

    def deleteUpload(self,upload:"Upload"):
        if upload.uploader==self or (self in upload.room.admins.all() and upload.uploader not in upload.room.admins.all()) or self==upload.room.creator:
            upload.delete()
        else:
            return "This upload isn't yours to delete."
        
    def joinRoom(self,room:"Room",password=""):
        return room.join(self,password)

    def dcRoom(self,room:"Room"):
        return room.dc(self)

    def kickUser(self,room:"Room",user):
        if self!=user:
            return room.kick(self,user)
        else:
            return "Need diffrent user."

    def banUser(self,room:"Room",user):
        if self!=user:
            return room.ban(self,user)
        else:
            return "Need diffrent user."

    def makeUserAdmin(self,room:"Room",user):
        if self!=user:
            return room.makeAdmin(self,user)
        else:
            return "Need diffrent user."

    def removeUserAdmin(self,room:"Room",user):
        if self!=user:
            return room.removeAdmin(self,user)
        else:
            return "Need diffrent user."            
    
    def inviteUser(self,room:"Room",user):
        if self!=user:        
            return room.invite(self,user)
        else:
            return "Need diffrent user."            

class Room(models.Model):
    name = models.CharField(max_length=150)
    members = models.ManyToManyField(
        get_user_model(), blank=True, editable=False, related_name="member_of"
    )
    limit = models.PositiveSmallIntegerField("Member limit")
    creator = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="creator_of"
    )
    bans = models.ManyToManyField(
        get_user_model(), blank=True, related_name="banned_from",editable=False
    )
    invites = models.ManyToManyField(
        get_user_model(), blank=True, related_name="invited_to",editable=False
    )
    admins = models.ManyToManyField(
        get_user_model(), blank=True, related_name="admin_of",editable=False
    )
    code = models.CharField(max_length=36, blank=True, null=True, unique=True, editable=False)
    expire_date = models.DateTimeField(null=True,blank=True, editable=False)
    welcome_text = models.TextField("Welcome message", blank=True)
    has_password = models.BooleanField(default=False)
    password = models.CharField(max_length=32, blank=True)
    is_private = models.BooleanField(default=False)
    can_invite = models.BooleanField(default=True)
    can_admins_invite = models.BooleanField(default=True)
    can_upload = models.BooleanField(default=True)
    can_admins_upload = models.BooleanField(default=True)

    @property
    def member_count(self):
        return self.members.count()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name','creator'],name="name and creator unique")
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.limit < 1 or self.limit > 100 or self.limit is None:
            raise ValidationError("Limit must be between 1 and 100.")
        if (self.has_password == False and self.password != "") or (
            self.has_password == True and self.password == ""
        ):
            raise ValidationError("Incorrect value for the room's password.")
    
    def join(self,user,password=""):                
        if user not in self.members.all():            
            if self.members.count()<self.limit:     
                if user not in self.bans.all():      
                    if (user in self.invites.all() and self.can_invite==True) or user in self.admins.all():
                        if self.members.count()==0:
                            self.expire_date=None
                            self.save()
                        if user in self.invites.all():
                            self.invites.remove(user)
                        self.members.add(user)
                    elif (self.has_password==True and self.password==password) or self.has_password==False:
                        if self.members.count()==0:
                            self.expire_date=None
                            self.save()
                        self.members.add(user)
                    else:
                        return "Couldn't join room."
                else:
                    return "You are banned from this room."
            else:
                return "Room member limit reached."
        else:
            return "Already in room."
        
    def dc(self,user):
        if user in self.members.all():
            self.members.remove(user)
            if self.members.count()==0:
                self.expire_date=now()+datetime.timedelta(days=3)
                self.save()
        else:
            return "Not in room in order to disconnect."
        
    def kick(self,u1,u2):
        if u1 in self.members.all() and u2 in self.members.all():
            if u1==self.creator:
                self.members.remove(u2)
            elif u1 in self.admins.all() and u2 not in self.admins.all():
                self.members.remove(u2)
            else:
                return "You need to be an admin in order to kick a non admin user."
        else:
            return "You and the user that is going to be kicked need to be in the room."
        
    def ban(self,u1,u2):
        if u1 in self.members.all() and u2 in self.members.all():
            if u1==self.creator:
                self.members.remove(u2)
                self.bans.add(u2)
                if u2 in self.admins.all():
                    self.admins.remove(u2)
            elif u1 in self.admins.all() and u2 not in self.admins.all():
                self.members.remove(u2)
                self.bans.add(u2)
            else:
                return "You need to be an admin in order to ban a non admin user."
        else:
            return "You and the user that is going to be banned need to be in the room."
        
    def makeAdmin(self,u1,u2):
        if u1==self.creator and u2 not in self.bans.all() and u2 in self.members.all() and u1 in self.members.all() and u2 not in self.admins.all():
            self.admins.add(u2)
        else:
            return "You need to be the creator of the room and be in the room along with the selected user (the other user shouldn't be banned)."
        
    def removeAdmin(self,u1,u2):
        if u1==self.creator and u2 in self.members.all() and u1 in self.members.all() and u2 in self.admins.all():
            self.admins.remove(u2)
        else:
            return "You need to be the creator of the room and be in the room along with the selected user."
        
    def invite(self,u1,u2):
        if u1 in self.members.all() and u2 not in self.members.all() and u2 in u1.friends.all() and u2 not in self.bans.all():
            if u1==self.creator:
                self.invites.add(u2)
            elif u1 in self.admins.all() and self.can_admins_invite==True:
                self.invites.add(u2)
            elif u1 not in self.admins.all() and self.can_invite==True:
                self.invites.add(u2)
            else:
                return "This room doesn't allow you to invite."
        else:
            return "You need to be in the room and friends with the selected user which shouldn't be in the room and banned from the room."


def uploadPath(instance:"Upload",filename):
    return f"{instance.room.id}/{filename}"

class Upload(models.Model):
    file = models.FileField(upload_to=uploadPath)
    dname = models.CharField("Download name",max_length=32, blank=True)
    caption = models.CharField(max_length=150, blank=True)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="files")
    uploader = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="files"
    )

    def __str__(self):
        return f"{self.dname} in {self.room.name}"
    
    def clean(self):
        if self.dname=="" or self.dname is None:
            self.dname=self.file.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['dname','room'],name="upload and room unique")
        ]

class FriendRequest(models.Model):
    sender = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,related_name="fr_sent")
    receiver = models.ForeignKey(get_user_model(), on_delete=models.CASCADE,related_name="fr_received")

    def __str__(self):
        return f"{self.sender} to {self.receiver}"

    def accept(self):
        self.sender.friends.add(self.receiver)
        self.delete()

    def decline(self):
        self.delete()

    def clean(self):
        if FriendRequest.objects.filter(receiver=self.sender,sender=self.receiver).count() > 0:
            raise ValidationError("Friend request already exists.")
        if self.receiver in self.sender.friends.all():
            raise ValidationError("Already friends with this user.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['sender','receiver'],name="Friend request unique")
        ]