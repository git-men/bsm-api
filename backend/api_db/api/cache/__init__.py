from django.core.cache import cache
from django.conf import settings


class BaseCache:
    """缓存基础类"""

    def set_cache(self, key, content, pipe=None):
        key = cache.make_key(key)
        cache_time = getattr(settings, 'API_CACHE_TIME', 1 * 60)
        cache.set(key, content, cache_time)

    def get_cache(self, key, pipe=None):
        key = cache.make_key(key)
        return cache.get(key)

    def delete_cache(self, key, pipe=None):
        key = cache.make_key(key)
        cache.delete(key)


class ApiCache(BaseCache):
    API_KEY = "api:slug:{}"

    def set_api_config(self, slug, api_config, pipe=None):
        """缓存api配置"""
        self.set_cache(self.API_KEY.format(slug), api_config, pipe)

    def get_api_config(self, slug, pipe=None):
        """读api缓存"""
        return self.get_cache(self.API_KEY.format(slug), pipe)

    def delete_api_config(self, slug, pipe=None):
        """清api缓存"""
        self.delete_cache(self.API_KEY.format(slug), pipe)


api_cache = ApiCache()
