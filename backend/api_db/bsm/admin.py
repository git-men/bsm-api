from django.conf import settings
from api_basebone.core.admin import BSMAdmin, register
from api_db.models import Api, Function, FunctionParameter


@register
class FunctionAdmin(BSMAdmin):
    modal_form = False
    display = ['name', 'model', 'scene', 'login_required', 'staff_required', 'superuser_required', 'enable']
    form_fields = ['name',     
    {'name': 'model', 'widget': 'ModelSelect'},
    'scene', 'login_required', 'staff_required', 'superuser_required', 'roles', 'enable', 
    'description',
    {'name': 'code', 'widget': 'CodeEditor'}, 
    {'name': 'functionparameter', 'widget': 'InnerTable', 'params': {'canAdd': True}}]
    inline_actions = ['edit', 'delete']
    form_layout = {
        'style': 'group',
        'sections': [
            {
                'title': '基本信息',
                'fields': ['name', 'model', 'scene', 'login_required', 'staff_required', 'superuser_required', 'roles', 'enable', 'description']
            },
            {
                'title': '参数',
                'fields': ['functionparameter']
            },
            {
                'title': '代码',
                'fields': ['code']
            }
        ]
    }

    class Meta:
        model = Function


@register
class FunctionParamAdmin(BSMAdmin):
    form_fields = [
        'name', 'display_name', 'type',
        {'name': 'ref', 'widget': 'ModelSelect', 'show': '${type} === "ref"'},
        'required', 'description'
    ]
    display = ['name', 'display_name', 'type', 'ref', 'required', 'description']

    class Meta:
        model = FunctionParameter


@register
class APIAdmin(BSMAdmin):
    modal_form = False
    form_fields = ['operation']
    display = ['id', 'operation', 'slug', 'name']
    inline_actions = [
        'edit', 'delete',
        {
            'type': 'info',
            'title': '请求地址',
            'params': {'title': '查看请求地址', 'content': settings.API_BASE_URL + '/${slug}/'},
        },
        {
            'type': 'link',
            'title': '查看文档',
            'params': {'link': settings.API_DOC_BASE_URL + '/#/default/${slug}'},
        },
    ]
    table_actions = [
        {
            'icon': 'plus',
            'title': '新建',
            'submenus': [
                {
                    'title': '列表接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=list'},
                },
                {
                    'title': '详情接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=retrieve'},
                },
                {
                    'title': '新建接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=create'},
                },
                {
                    'title': '删除接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=delete'},
                },
                {
                    'title': '全部更新接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=update'},
                },
                {
                    'title': '部分更新接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=replace'},
                },
                {
                    'title': '云函数接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=func'},
                },
                {
                    'title': '批量删除接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=delete_by_condition'},
                },
                {
                    'title': '批量更新接口',
                    'type': 'link',
                    'params': {'link': '/content/api_db__api/add?operation=update_by_condition'},
                },
            ]
        }
    ]

    class Meta:
        model = Api
