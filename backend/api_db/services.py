from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from .models import Api


def create_api_permission(api: Api):
    if api.permission:
        return
    ctype = ContentType.objects.filter(app_label=api.app, model=api.model).first()
    p = Permission()
    p.name = f'执行 api.{api.slug}'
    p.content_type = ctype
    p.codename = f'api.{api.slug}'
    p.save()
    api.permission = p
