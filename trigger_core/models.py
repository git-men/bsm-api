import logging
import uuid

from . import const

from django.db import models
from api_basebone.core.fields import JSONField

logger = logging.getLogger('django')


def UUID():
    return uuid.uuid4().hex


class Trigger(models.Model):
    '''触发器'''

    slug = models.SlugField('标识', max_length=50, unique=True, default=UUID)
    name = models.CharField('名称', max_length=50, default='')
    summary = models.TextField('api说明', default='')
    event = models.CharField('操作', max_length=20, choices=const.TRIGGER_EVENT_CHOICES)
    disable = models.BooleanField('停用', default=False)

    def __str__(self):
        return '%s object (%s,%s,%s)' % (
            self.__class__.__name__,
            self.pk,
            self.slug,
            self.event,
        )

    class Meta:
        verbose_name = '触发器'
        verbose_name_plural = '触发器'


class TriggerCondition(models.Model):
    """触发器条件"""

    trigger = models.OneToOneField(
        Trigger, models.CASCADE, verbose_name='trigger_condition'
    )
    app = models.CharField('app名字', max_length=50, null=True)
    model = models.CharField('数据模型名字', max_length=50, null=True)
    filters = JSONField('筛选条件', default=[], blank=True)

    def __str__(self):
        return '%s object (%s,%s,%s)' % (
            self.__class__.__name__,
            self.pk,
            self.app,
            self.model,
        )

    class Meta:
        verbose_name = '触发器条件'
        verbose_name_plural = '触发器条件'

        index_together = [('app', 'model')]


class TriggerAction(models.Model):
    '''触发器行为'''

    trigger = models.ForeignKey(Trigger, models.CASCADE, verbose_name='trigger')
    action = models.CharField('条件类型', max_length=20, choices=const.TRIGGER_ACTION_CHOICES)
    app = models.CharField('app名字', default='', max_length=50)
    model = models.CharField('数据模型名字', default='', max_length=50)
    fields = JSONField('操作的属性', default={}, blank=True)
    filters = JSONField('操作的条件', default=[], blank=True)

    class Meta:
        verbose_name = '触发器行为'
        verbose_name_plural = '触发器行为'
