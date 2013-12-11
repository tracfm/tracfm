from django.core.urlresolvers import reverse
from .models import Campaign, CampaignImage
from smartmin.views import SmartCRUDL, SmartListView, SmartCreateView, SmartUpdateView, SmartDeleteView

class CampaignCRUDL(SmartCRUDL):
    model = Campaign
    permissions = True
    actions = ('create', 'read', 'update', 'list', 'delete', 'public')

    class Update(SmartUpdateView):
        delete_url = "id@campaigns.campaign_delete"
        exclude = ('is_active','created_by', 'modified_by',)

    class Public(SmartListView):
        fields = ('name', 'description')
        model = Campaign
        template_name = 'campaigns/campaign_list.html'
        permission = None

        def get_queryset(self, **kwargs):
            queryset = super(CampaignCRUDL.Public, self).get_queryset(**kwargs)
            return queryset.order_by("-priority")        

    class List(SmartListView):
        fields = ('name','description')

        def get_queryset(self, **kwargs):
            queryset = super(CampaignCRUDL.List, self).get_queryset(**kwargs)
            return queryset.order_by("-priority")

class CampaignImageCRUDL(SmartCRUDL):
    model = CampaignImage
    permissions = True
    actions = ('create', 'update', 'list', 'delete')

    class Delete(SmartDeleteView):
        name_field = 'caption'
        def get_redirect_url(self, **kwargs):
            return reverse("campaigns.campaign_update", args=[self.object.campaign.pk])
        def get_cancel_url(self):
            return reverse("campaigns.campaignimage_update", args=[self.object.pk])

    class Update(SmartUpdateView):
        fields = ('image', 'caption', 'priority')
        delete_url = "id@campaigns.campaignimage_delete"
        def get_success_url(self):
            return reverse("campaigns.campaign_update", args=[self.object.campaign.pk])

    class Create(SmartCreateView):
        fields = ('image', 'caption', 'priority')

        def get_success_url(self):
            return reverse("campaigns.campaign_read", args=[self.request.REQUEST['campaign']])

        def derive_initial(self):
            initial = dict()
            if 'campaign' in self.request.REQUEST:
                initial['campaign'] = self.request.REQUEST['campaign']
            return initial

        def pre_save(self, obj):
            obj.campaign = Campaign.objects.get(pk=self.request.REQUEST['campaign'])
            obj.width = obj.image.width
            obj.height = obj.image.height
            return obj
