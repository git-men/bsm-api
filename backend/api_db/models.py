import logging
import uuid

from django.db import models
from api_basebone.core.fields import JSONField
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group
from api_core.api import const


logger = logging.getLogger('django')


class Api(models.Model):
    '''Api接口模型'''

    slug = models.SlugField('接口标识', max_length=50, unique=True)
    app = models.CharField('app名字', max_length=50)
    model = models.CharField('数据模型名字', max_length=50)
    name = models.CharField('名称', max_length=50, default='')
    operation = models.CharField('操作', max_length=20, choices=const.OPERATIONS_CHOICES)
    ordering = models.CharField('排序', max_length=500, blank=True, default='')
    expand_fields = models.CharField('展开字段', max_length=500, blank=True, default='')
    func_name = models.CharField('云函数名称', max_length=50, blank=True, default='')
    summary = models.TextField('api说明', default='')
    demo = models.TextField('api返回格式范例', default='')
    config = models.TextField('配置json数据', default='')

    disable = models.BooleanField('停用', default=False)
    logined = models.BooleanField('要求登录', default=True)
    permission = models.OneToOneField(
        Permission,
        verbose_name='权限',
        on_delete=models.CASCADE,
        related_name='api',
        null=True,
        blank=True,
    )
    groups = models.ManyToManyField(Group, verbose_name='角色', blank=True)

    def __str__(self):
        return self.slug

    @property
    def method(self):
        '''API提交的方法'''
        return const.METHOD_MAP.get(self.operation)

    @property
    def expand_fields_set(self):
        '''展开字段的集合'''
        if self.expand_fields:
            return set(self.expand_fields.replace(' ', '').split(','))
        else:
            return set()

    def method_equal(self, method):
        return method.lower() in self.method

    def get_order_by_fields(self):
        if self.ordering:
            return self.ordering.replace(' ', '').split(',')
        else:
            return set()

    class Meta:
        verbose_name = 'Api接口模型'
        verbose_name_plural = 'Api接口模型'

        index_together = [("app", "model")]

    class GMeta:
        exclude_fields = ['config']


class Parameter(models.Model):
    '''参数'''

    TYPE_STRING = 'string'
    TYPE_INT = 'int'
    TYPE_DECIMAL = 'decimal'
    TYPE_BOOLEAN = 'boolean'
    TYPE_JSON = 'json'
    TYPE_OBJECT = 'object'
    TYPE_PAGE_SIZE = 'PAGE_SIZE'
    TYPE_PAGE_IDX = 'PAGE_IDX'
    TYPE_PK = 'pk'
    TYPES_CHOICES = (
        (TYPE_STRING, '字符串'),
        (TYPE_INT, '整数'),
        (TYPE_DECIMAL, '浮点数'),
        (TYPE_BOOLEAN, '布尔值'),
        (TYPE_JSON, 'json格式'),
        (TYPE_OBJECT, '复杂类型'),
        (TYPE_PAGE_SIZE, '页长'),
        (TYPE_PAGE_IDX, '页码'),
        (TYPE_PK, '主键'),
    )
    TYPES = set([t[0] for t in TYPES_CHOICES])

    SPECIAL_TYPES = (TYPE_PAGE_SIZE, TYPE_PAGE_IDX, TYPE_PK)

    api = models.ForeignKey(Api, models.CASCADE, verbose_name='api')
    name = models.CharField('参数名', max_length=50)
    desc = models.CharField('备注', max_length=100)
    type = models.CharField('参数类型', max_length=20, choices=TYPES_CHOICES)
    required = models.BooleanField('是否必填', default=True)
    default = models.CharField('默认值', max_length=50, null=True)
    use_default = models.BooleanField('是否使用默认值', default=True)
    is_array = models.BooleanField('是否数组', default=False)

    parent = models.ForeignKey(
        'self', models.CASCADE, null=True, verbose_name='parent', related_name="children"
    )
    layer = models.IntegerField('嵌套层数', default=0)

    def to_set_field_config(self):
        config = {'name': self.name, 'value': f'${{{self.name}}}'}
        if hasattr(self, 'children'):
            config['children'] = [
                p.to_set_field_config()
                for p in self.children.all()
                if not p.is_special_defined()
            ]
        return config

    def is_special_defined(self):
        """自定义参数，用于特殊用途"""
        return self.type in const.SPECIAL_TYPES

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '参数'
        verbose_name_plural = '参数'


class DisplayField(models.Model):
    '''API的字段'''

    api = models.ForeignKey(Api, models.CASCADE, verbose_name='api')
    name = models.CharField('字段名', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'API的查询字段'
        verbose_name_plural = 'API的查询字段'
        ordering = ['name']  # 排序很重要，确保同一个分支的列会排在一起，且层级少的排在前面


class SetField(models.Model):
    '''API的字段'''

    api = models.ForeignKey(Api, models.CASCADE, verbose_name='api')
    name = models.CharField('字段名', max_length=100)
    value = models.CharField('赋值', max_length=200)

    parent = models.ForeignKey(
        'self', models.CASCADE, null=True, verbose_name='parent', related_name="children"
    )
    layer = models.IntegerField('嵌套层数', default=0)

    def __str__(self):
        return f'SetField:{self.api}, {self.name}, {self.value}'

    class Meta:
        verbose_name = 'API的赋值字段'
        verbose_name_plural = 'API的赋值字段'
        ordering = ['name']  # 排序很重要，确保同一个分支的列会排在一起，且层级少的排在前面


class Filter(models.Model):
    '''查询条件'''

    api = models.ForeignKey(Api, models.CASCADE, verbose_name='api')
    type = models.IntegerField(
        '条件类型',
        choices=((const.FILTER_TYPE_CONTAINER, '容器'), (const.FILTER_TYPE_CHILD, '单一条件')),
    )
    parent = models.ForeignKey(
        'self', models.CASCADE, null=True, verbose_name='parent', related_name="children"
    )
    field = models.CharField('条件字段名', max_length=50, null=True)
    # operator = models.CharField('条件判断符', max_length=20, choices=OPERATIONS_CHOICES)
    operator = models.CharField('条件判断符', max_length=20)
    value = models.CharField('条件值', max_length=100, null=True)
    layer = models.IntegerField('嵌套层数', default=0)

    def __str__(self):
        if self.type == const.FILTER_TYPE_CONTAINER:
            return f'{self.operator}'
        elif self.type == const.FILTER_TYPE_CHILD:
            return f'{self.field} {self.operator} {self.value}'
        else:
            return ''

    class Meta:
        verbose_name = 'API的查询条件'
        verbose_name_plural = 'API的查询条件'