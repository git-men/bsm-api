from django.db.models.signals import post_save
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Api
from . import services


@receiver(pre_save, sender=Api, dispatch_uid='create_api_permission')
def create_api_permission(sender, instance: Api, **kwargs):
    """保存前创建权限数据"""
    if not instance.permission:
        services.create_api_permission(instance)


@receiver(post_save, sender=Api, dispatch_uid='update_api_groups')
def update_api_groups(sender, instance: Api, **kwargs):
    # 有主键才能加载多对多，所以用post_save
    if set(instance.permission.group_set.all()) != set(instance.groups.all()):
        instance.permission.group_set.set(instance.groups.all())
        instance.permission.save()
