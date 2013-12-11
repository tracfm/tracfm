from django.contrib.auth.models import User, Group
from rapidsms_httprouter.models import Message
from django import forms

from smartmin.views import *
from django_quickblocks.models import QuickBlock
from django.http import Http404

class StoryListView(TemplateView):

    def get_template_names(self):
        return ['stories/%s_list.html' % self.type, 'stories/list.html']

    def get_context_data(self,  **kwargs):
        if 'type' in kwargs:
            self.type = kwargs['type']
            content_type = QuickBlockType.objects.get(slug=self.type.lower())
            quickblocks = QuickBlock.objects.filter(is_active=True,
                                                    quickblock_type=content_type).order_by('-priority')
            return dict(quickblocks=quickblocks, quickblock_type=self.type)
        raise Http404(u"Invalid story type")

class StoryView(TemplateView):
    template_name="story.html"

    def get_template_names(self):
        return ['stories/%s_read.html' % self.tag, 'stories/read.html']

    def get_context_data(self,  **kwargs):
        if 'id' in kwargs:
            self.type = kwargs['type']
            id = kwargs['id']
            quickblock = QuickBlock.objects.get(id=id)

            return dict(story=quickblock, quickblock_type=self.type)
        raise Http404(u"Invalid story page")

