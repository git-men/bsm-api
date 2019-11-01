from django.urls import path, include

app_name = 'api_common'


urlpatterns = [
    # 配置API接口处理器
    path('api/', include(('api_core.api.urls', app_name), namespace='api')),
    # 配置API接口帮助文档配置
    path('api_doc/', include(('api_core.api.doc_urls', app_name), namespace='api_doc')),
]
