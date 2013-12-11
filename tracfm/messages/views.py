from django import forms
from django.contrib.auth.models import User, Group
from django.views.generic.edit import FormMixin
from django.core.urlresolvers import reverse
from django.db.models import Q

from rapidsms_httprouter.models import Message
from rapidsms_httprouter.router import get_router

from smartmin.views import *

class MessageListView(SmartListView):
    permission = 'rapidsms_httprouter.message_list'
    model = Message
    fields = ('sms_dir', 'connection', 'text', 'status', 'date')
    template_name = 'messages/list.html'
    link_fields = ()
    search_fields = ('text__icontains','connection__identity__icontains', 'in_response_to__text__icontains')
    refresh = 10000

    field_config = {
        'sms_dir': dict(label=""),
        'connection': dict(label="Phone"),
        'text': dict(label="Message"),
    }

    def get_sms_dir(self, obj):
        return "<div class='" + obj.direction + "'></div>"

    def get_connection(self, obj):
        if self.request.user.has_perm('rapidsms_httprouter.message_read'):
            return obj.connection.identity
        else:
            str_len = len(obj.connection.identity)
            return "#" * (str_len - 4) + obj.connection.identity[-4:]

    def get_queryset(self, **kwargs):
        queryset = super(MessageListView, self).get_queryset(**kwargs)

        # ingore demographic polls
        queryset = queryset.exclude(pollresponse__poll__demographic=True)

        # if we have full view permissions, we can see all messages
        if self.request.user.has_perm('rapidsms_httprouter.message_read'):
            return queryset.order_by('-pk')

        # otherwise, we only show those messages from polls the user owns
        else:
            query = Q(pollresponse__poll__user=self.request.user)
            query |= Q(in_response_to__pollresponse__poll__user=self.request.user)
            return queryset.filter(query)

class SendForm(forms.Form):
    sender = forms.CharField(max_length=20)
    text = forms.CharField(max_length=160, min_length=1)

class MessageSendView(MessageListView, FormMixin):
    model = Message
    permission = 'rapidsms_httprouter.message_send'
    form_class = SendForm

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            message = get_router().handle_incoming('console',
                                                   form.cleaned_data['sender'],
                                                   form.cleaned_data['text'])
            return self.form_valid(form)
        else:
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data(form=form, object_list=self.object_list))

    def get_success_url(self):
        return reverse("messages")


