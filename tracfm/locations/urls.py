from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^$', LocationTypeListView.as_view(), name="location_types"),
    url(r'^add/$', LocationTypeCreateView.as_view(), name="add_location_type"),
    url(r'^view/(?P<pk>\d+)/$', LocationListView.as_view(), name="list_locations"),
    url(r'^view/(?P<areatype_id>\d+)/(?P<pk>\d+)/$', LocationUpdateView.as_view(), name="edit_location"),
    url(r'^del/(?P<areatype_id>\d+)/(?P<pk>\d+)/$', LocationDeleteView.as_view(), name="delete_location"),
    url(r'^add/(?P<areatype_id>\d+)/$', LocationCreateView.as_view(), name="add_location"),
    url(r'^edit/(?P<pk>\d+)/$', LocationTypeUpdateView.as_view(), name="edit_location_type"),
)
