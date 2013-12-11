from views import *
from django.conf.urls.defaults import *

urlpatterns = CampaignCRUDL().as_urlpatterns()
urlpatterns += CampaignImageCRUDL().as_urlpatterns()
