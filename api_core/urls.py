import os
from django.urls import path, include

from django.views import static
from django.conf.urls import url

app_name = 'api_common'

document_root = os.path.dirname(os.path.abspath(__file__)) + '/doc_static'

urlpatterns = [
    # 配置API接口处理器
    path('api/', include(('api_core.api.urls', app_name), namespace='api')),
    # 配置API接口帮助文档配置
    path('api_doc/', include(('api_core.api.doc_urls', app_name), namespace='api_doc')),
    # 静态资源
    url(
        r'api_doc/static/(?P<path>.*)$',
        static.serve,
        {'document_root': document_root, 'show_indexes': False},
        name='api_static',
    ),
]
