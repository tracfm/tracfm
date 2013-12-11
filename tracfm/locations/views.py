from simple_locations.models import AreaType, Point
from models import Area
from smartmin.views import *

from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.forms.models import ModelForm
from django import forms

class LocationTypeListView(SmartListView):
    permission = 'simple_locations.list_areatype'
    model = AreaType
    add_button = True
    link_fields = ('name',)
    fields = ('name', 'slug', 'location_count')

    def get_location_count(self, obj):
        return obj.area_set.all().count()

    field_config = {
        'location_count': dict(label="Locations")
    }
    

field_config = {
    'name': dict(help="The name for this category.  This can contain spaces"),
    'slug': dict(help="A simple name for this category, cannot contain space, only letters, numbers or undescores.")
}


type_field_config = {
    'name': dict(help="The name for this category.  This can contain spaces"),
    'slug': dict(help="A simple name for this category, cannot contain space, only letters, numbers or undescores.")
}

area_field_config = {
    'name': dict(help="Enter the official name for the location."),
    'rules': dict(help="What words will cause a response to match this location.  "
                  "Messages must contain all the words on a line.")
}

class LocationTypeCreateView(SmartCreateView):
    model = AreaType
    success_url = "/locations/"
    permission = 'simple_locations.add_areatype'
    grant_permissions = ('simple_locations.change_areatype',)
    field_config = type_field_config

class LocationTypeUpdateView(SmartUpdateView):
    model = AreaType
    success_url = "/locations/"
    permission = 'simple_locations.change_areatype'
    field_config = type_field_config

class LocationListView(SmartListView):
    permission = 'locations.list_area'
    model = Area
    link_fields = ('name',)
    link_url = ""
    template_name = 'locations/list.html'
    fields = ('name', 'rules', 'location')

    def get_rules(self, obj):
        return ", ".join([rule.match for rule in obj.rules.all()])

    def get_queryset(self):
        queryset = super(LocationListView, self).get_queryset()
        self.extra_context['areatype'] = AreaType.objects.get(pk=self.kwargs['pk'])
        self.extra_context['form'] = LocationForm
        return queryset.filter(kind__id=self.kwargs['pk'])

class LocationForm(ModelForm):
    class Meta:
        model = Area

    rules = forms.CharField(widget=forms.Textarea, required=False)

class LocationUpdateView(SmartUpdateView):
    model = Area
    form_class = LocationForm
    permission = 'locations.change_area'
    field_config = area_field_config
    fields = ('name','rules')
    template_name = "locations/update_location.html"

    def get_initial(self):
        """
        Patch in our initial value for our rules
        """
        initial = super(LocationUpdateView, self).get_initial()
        initial['rules'] = self.object.get_rules()
        return initial

    def pre_save(self, obj):
        """
        Set's our rules before saving.
        """
        super(LocationUpdateView, self).pre_save(obj)        
        obj.set_rules(self.form.cleaned_data['rules'])
        return obj

    def get_success_url(self):
        return reverse('list_locations', args=[self.kwargs['areatype_id']])

class LocationForm(ModelForm):

    class Meta:
        model = Area
        exclude = ('rules', 'kind', 'code', 'location', 'parent')
        
    name = forms.CharField()
    latitude = forms.CharField()
    longitude = forms.CharField()
    
class LocationCreateView(SmartCreateView):
        
    model = Area
    fields = ('name',)
    permission = 'locations.add_area'
    form_class = LocationForm
    
    def pre_save(self, obj):
        super(LocationCreateView, self).pre_save(obj)
        
        obj.kind = get_object_or_404(AreaType, id=self.kwargs['areatype_id'])

        lat = self.form.cleaned_data['latitude']
        lng = self.form.cleaned_data['longitude']

        # set an initial our rule based on our name
        obj.set_rules(obj.name.lower())

        if lat and lng:
            location=Point(latitude=lat,longitude=lng)
            location.save()
            obj.location=location

        return obj

    def get_success_url(self):
        return reverse("list_locations", args=[self.kwargs['areatype_id']])


import django.dispatch
location_deleted = django.dispatch.Signal(providing_args=["location", "delete_deep"])

class LocationDeleteView(SmartDeleteView):
    model = Area
    permission = 'locations.change_area'
    template_name = "locations/delete_location.html"

    def pre_delete(self, request):
        location = self.get_object()

        # trigger our location deletion signal
        location_deleted.send(self, location=location, delete_deep=request.POST['delete_deep'] == 'delete')


    def get_cancel_url(self):
        return "/locations/view/%(areatype_id)s/" % self.kwargs

    def get_redirect_url(self):
        return "/locations/view/%(areatype_id)s/" % self.kwargs
