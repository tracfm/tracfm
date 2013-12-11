from django.conf.urls.defaults import *

from .views import *

urlpatterns = patterns('',
    url(r'^send/$', MessageSendView.as_view(), name="messages_send"),                       
    url(r'^$', MessageListView.as_view(), name="messages"),
)
