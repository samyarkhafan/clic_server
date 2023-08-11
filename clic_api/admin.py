from typing import Any
from django.contrib import admin
from .models import Room,FriendRequest,Upload
from django.contrib.auth import get_user_model

# Register your models here.
class RoomAdmin(admin.ModelAdmin):
    exclude=["admins"]

admin.site.register(Room, RoomAdmin)
admin.site.register(FriendRequest)
admin.site.register(Upload)
admin.site.register(get_user_model())