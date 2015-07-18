from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.i18n import javascript_catalog


from rest_framework import routers

from services.views import ItemViewSet
from frontend.views import UserUpdate, SearchItemsListView

# django admin
admin.autodiscover()

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'items', ItemViewSet, 'Item')

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('myproject'),
}

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'frontend.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/',include(router.urls)),
    url(r'^api-auth/',include('rest_framework.urls', namespace='rest_framework')),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^oauth/', include('oauth.urls')),
    url('', include('django.contrib.auth.urls', namespace='auth')),
    url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'^accounts/profile/', UserUpdate.as_view(success_url="/"), name='profile'),
    url(r'^request/(?P<id>[\d+]{1,40})/$', 'frontend.views.request_item', name='request_item'),
    url(r'^vote/(?P<id>[\d+]{1,40})/$', 'frontend.views.vote_user', name='vote_user'),
    url(r'^search/$', SearchItemsListView.as_view(), name='search'),
    url(r'^thumb/(?P<shape>\w+)/(?P<id>\d+)/(?P<width>\d+).png$', 'frontend.views.image_on_demand', name="thumb"),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^jsi18n/$', javascript_catalog, js_info_dict),
)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

