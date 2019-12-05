from api_basebone.drf.routers import BaseBoneSimpleRouter as SimpleRouter
from .doc_views import ApiDocViewSet

router = SimpleRouter(custom_base_name='api_doc')
router.register('', ApiDocViewSet)
print(f'router.urls:{router.urls}')

urlpatterns = router.urls
