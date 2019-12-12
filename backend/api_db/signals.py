from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Api
from . import services


@receiver(pre_save, sender=Api, dispatch_uid='create_api_permission')
def create_api_permission(sender, instance: Api, **kwargs):
    """创建权限数据"""
    if not instance.permission:
        instance.is_staff = True
        services.create_api_permission(instance)
