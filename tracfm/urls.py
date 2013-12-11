from django.conf.urls.defaults import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
admin.autodiscover()

from .views import *
from django_quickblocks.stories.views import StoryListView

urlpatterns = patterns('',
    # Example:
    # (r'^tracfm/', include('tracfm.foo.urls')),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),

    # homepage shows 'home' stories
    (r'^$', StoryListView.as_view(), { 'type': 'home' }, 'public_index'),

    # additional story sites
    url(r'^s/', include('django_quickblocks.stories.urls')),

    # polls
    url(r'^p/', include('polls.urls')),

    url(r'^c/', include('campaigns.urls')),

    # user list
    url(r'^users/', include('trac_users.urls')),

    # quickblocks
    url(r'^qbs/', include('django_quickblocks.urls')),

    # locations
    url(r'^locations/', include('locations.urls')),                       

    # admin site
    url(r'^admin/', include(admin.site.urls)),

    # router 
    url(r'', include('rapidsms_httprouter.urls')),

    # console                      
    url('^console/', include('nsms.console.urls')),
)

urlpatterns += staticfiles_urlpatterns()

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
              'document_root': settings.MEDIA_ROOT,
        }),
    )

