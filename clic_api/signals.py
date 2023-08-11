from django.dispatch import receiver
from django.db import models
from .models import Room
import uuid
import datetime
from django.utils.timezone import now

@receiver(models.signals.post_save,sender=Room, dispatch_uid="generate code and add creator",weak=False)
def roomPostSave(sender,instance:Room,**kwargs):
    if instance.code is None:
        instance.admins.add(instance.creator)
        instance.code=uuid.uuid4()
        instance.expire_date=now()+datetime.timedelta(days=3)
        instance.save()