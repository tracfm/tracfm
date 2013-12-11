from smartmin.views import *
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django import forms
from django.forms import ModelForm
from .models import *
from guardian.shortcuts import get_objects_for_user, assign, remove_perm
from guardian.core import ObjectPermissionChecker
from django.contrib.auth.models import Group
from rapidsms_httprouter.router import get_router
from rapidsms.messages.outgoing import OutgoingMessage
from django.http import Http404

def can_view_poll(user, poll):
    if user.has_perm('polls.poll_all'):
        return poll.user == user or user.backends.filter(backend=poll.backend)
    elif user.has_perm('polls.poll_read'):
        return poll.user == user or user.backends.filter(backend=poll.backend)
    else:
        return poll.is_public

def can_edit_poll(user, poll):
    if user.has_perm('polls.poll_all'):
        return poll.user == user or user.backends.filter(backend=poll.backend)
    elif user.has_perm('polls.poll_update'):
        return poll.user == user
    else:
        return False

class DemographicQuestionCRUDL(SmartCRUDL):
    permissions = True
    model = DemographicQuestion
    actions = ('create', 'update', 'list')

    class List(SmartListView):
        fields = ('question', 'created_on')

class SmartListUpdateView(SmartListView, ListView, ModelFormMixin, ProcessFormView):
    """
    SmartListUpdateView operates just like a SmartListView except it allows the implementor
    to wrap the entire list in a single form and declare which fields are mutable.
    """
    default_template = 'smartmin/list_update.html'
    required_fields = None
    update_fields = None

    def post(self, request, *args, **kwargs):
        """
        Override post so we can use the proper formset on submission.
        """
        form_class = self.get_form(self.get_form_class())
        self.form_post = form_class(request.POST)

        if self.form_post.is_valid():
            return self.form_valid(self.form_post)
        else:

            self.object_list = self.get_queryset()
            allow_empty = self.get_allow_empty()
            if not allow_empty and len(self.object_list) == 0:
                raise Http404(_(u"Empty list and '%(class_name)s.allow_empty' is False.") % {'class_name': self.__class__.__name__})

            context = self.get_context_data(object_list=self.object_list)
            context['formset'] = self.form_post
            return self.render_to_response(context)

    def is_field_required(self, field):
        """
        Determine if field is optional
        """
        try:
            if field.name in self.required_fields:
                return True
        except:
            pass

        return False

    def get_context_data(self, **kwargs):
        """
        Override context data so we can stuff in our formset and update fields.
        """
        context = super(SmartListUpdateView, self).get_context_data(**kwargs)
        form = self.get_form(self.get_form_class())
        context['formset'] = form(queryset=self.get_queryset())

        try:
            context['update_fields'] = self.update_fields
        except:
            pass

        return context

    def get_field_filter(self, field):
        return None

    def formfield_options(self, field):
        """
        Apply custom field options if any are specified. This method is called when
        the creates a FormSet based on our model for each field inside the model spec.
        """

        queryset = None
        if self.update_fields and field.name in self.update_fields:
            queryset = self.get_field_filter(field)

        if queryset:
            return field.formfield(queryset=queryset, required=self.is_field_required(field))
        else:
            return field.formfield(required=self.is_field_required(field))

    def get_success_url(self):
        """
        We override success url since we need to look inside our formset to get at
        an instance variable to use the absolute url if the success url is undefined.
        """
        if self.success_url:
            return self.success_url % self.object.__dict__
        else:
            try:
                if self.form_post.forms:
                    return self.form_post.forms[0].instance.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the Model.")

    def get_form(self, form_class):
        """
        Get a ModelFormSet for our specified model
        """
        # for now, we only work with models
        if not self.model:
            raise ImproperlyConfigured("SmartListUpdateView requires that a model be defined")

        # infer what our formset should be from the model and any other
        # provided configuration on our view

        update_fields = ()

        try:
            if self.update_fields:
                update_fields = self.update_fields
        except:
            pass

        self.form = model_forms.modelformset_factory(
            self.model,
            fields=update_fields,
            extra=0,
            formfield_callback=self.formfield_options)

        return self.form

class PollCategorySetListView(SmartListView):
    model = PollCategorySet
    add_button = True
    permission = 'polls.pollcategoryset_list'
    fields = ('name', 'description', 'owner')
    link_fields = ('name',)
    link_url = "id@catset_view"
    search_fields = ('name__icontains',)
    template_name = 'polls/catset_list.html'

    def derive_fields(self):
        fields = super(PollCategorySetListView, self).derive_fields()

        # if this user can create public templates, add a column
        if self.request.user.has_perm('polls.pollcategoryset_public'):
            fields = list(fields)
            fields.append('is_public')
        return fields

    def get_owner(self, obj):
        return obj.user

    def get_is_public(self, obj):
        if obj.is_public:
            return "<div class='public'></div>"
        return "<div class='private'></div>"

    def lookup_field_link(self, context, field, obj):
        return str(obj.id)

    def get_queryset(self):
        queryset = super(PollCategorySetListView, self).get_queryset().filter(poll=None).order_by('-is_public', '-user','name')
        if not self.request.user.has_perm('polls.pollcategoryset_update'):
            queryset = queryset.filter(Q(is_public=True)|Q(user=self.request.user.id))

        return queryset

class PollCategorySetForm(ModelForm):
    class Meta:
        model = PollCategorySet
    poll_template = forms.ModelChoiceField(queryset=Poll.objects.all().order_by("demographic"), required=False)

class PollCategorySetCreateView(SmartCreateView):
    model = PollCategorySet
    success_url = "id@catset_view"
    fields = ('name', 'description', 'poll_template')
    permission = 'polls.pollcategoryset_create'
    grant_permissions = ("polls.pollcategoryset_read", "polls.pollcategoryset_update")
    form_class = PollCategorySetForm

    field_config = {
        'poll_template': dict(label='Base on poll'),
    }

    def get_form(self, form_class):
        self.form = super(PollCategorySetCreateView, self).get_form(form_class)

        # if we are allowed, add option for making this template public
        if self.request.user.has_perm('polls.pollcategoryset_public'):
            is_public = forms.BooleanField(label='Public', required=False)
            self.form.fields['is_public'] = is_public

            if self.fields:
                self.fields += ('is_public',)

        return self.form

    def pre_save(self, obj):
        """
        We overload before saving to tie the object to the current user
        """
        obj.user = self.request.user
        return obj

    def post_save(self, obj):
        super(PollCategorySetCreateView, self).post_save(obj)
        if 'poll_template' in self.form.cleaned_data:
            obj.create_categories(self.form.cleaned_data['poll_template'])

        return obj

class PollCategorySetDetailView(SmartListView):
    model = PollCategory
    link_fields = ('name', 'count')
    pjax = '#bottom'
    template_name = "polls/catset_detail.html"
    permission = 'polls.pollcategoryset_read'

    field_config = {
        'get_rule_list': dict(label='Rules'),
        'count': dict(label='Count'),
        'location': dict(label='')
    }

    def lookup_field_link(self, context, field, obj):
        return reverse("category_edit", args=[obj.category_set.pk, obj.pk])

    def get_context_data(self, **kwargs):
        self.category_set = get_object_or_404(PollCategorySet, id=self.kwargs['pk'])
        context = super(PollCategorySetDetailView, self).get_context_data(**kwargs)

        if self.category_set.poll:
            context['base_url'] = reverse("poll_catset_view", kwargs=self.kwargs)
        else:
            context['base_url'] = reverse("catset_view", kwargs=self.kwargs)

        return context

    def derive_link_fields(self, context):

        # link the fields up if we have a global change permission
        if self.request.user.has_perm('polls.pollcategoryset_update'):
            return super(PollCategorySetDetailView, self).derive_link_fields(context)

        # link up if the user has permission on the specific template
        category_set = get_object_or_404(PollCategorySet, id=self.kwargs['pk'])
        checker = ObjectPermissionChecker(self.request.user)
        if checker.has_perm('polls.pollcategoryset_update', category_set):
            return super(PollCategorySetDetailView, self).derive_link_fields(context)

        # otherwise, don't link up anything
        return None

    def derive_fields(self):
        category_set = get_object_or_404(PollCategorySet, id=self.kwargs['pk'])
        if category_set.poll_id:
            return 'count', 'name', 'location', 'get_rule_list'
        else:
            return 'name', 'location', 'get_rule_list'

    def get_location(self, obj):
        loc = obj.location()
        if loc:
            return '<div class="loc_icon"></div>'
        else:
            return''

    def lookup_field_link(self, context, field, obj):

        if field == "name":
            if self.category_set.poll:
                return reverse("poll_category_edit", kwargs=dict(catset_id=obj.category_set.id, pk=obj.id))
            else:
                return reverse("category_edit", kwargs=dict(catset_id=obj.category_set.id, pk=obj.id))
        elif field == "count":
            return reverse("responses_for_poll", kwargs=dict(poll_id=obj.category_set.poll.id, category_id=obj.id))

    def get_queryset(self):
        category_set = get_object_or_404(PollCategorySet, id=self.kwargs['pk'])
        self.extra_context['pollcategoryset'] = category_set
        return category_set.categories.all().annotate(count=Count("primary_responses")).order_by("-count", "name")


class PollCategorySetUpdateView(SmartUpdateView):
    model = PollCategorySet
    permission = "polls.pollcategoryset_update"
    template_name = "polls/catset_update.html"

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(PollCategorySetUpdateView, self).has_permission(request, *args, **kwargs)
        if not has_perm:
            poll = self.get_object().poll
            if poll:
                has_perm = poll.user == self.request.user

        return has_perm

    def get_success_url(self):
        return "/p/catsets/%d/" % self.get_object().id

    def derive_fields(self):
        fields = super(PollCategorySetUpdateView, self).derive_fields()

        # if this user can create public polls, add a column
        if self.request.user.has_perm('polls.poll_public'):
            return ('name', 'description', 'is_public')
        else:
            return ('name', 'description')

class PollCategorySetDeleteView(SmartDeleteView):
    model = PollCategorySet
    permission = 'polls.pollcategoryset_delete'
    cancel_url = 'id@catset_view'
    redirect_url = "/p/catsets/"

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(PollCategorySetDeleteView, self).has_permission(request, *args, **kwargs)
        if not has_perm:
            poll = self.get_object().poll
            if poll:
                has_perm = poll.user == self.request.user

        return has_perm

class RespondentDetailView(SmartListView):
    model = PollResponse
    fields = ('poll', 'category', 'secondary_category', 'text', 'created')
    link_fields = ()
    template_name = 'polls/respondent_detail.html'
    permission = "polls.respondent_read"
    link_url = "id@respondent_edit"

    def lookup_field_value(self, context, obj, field):
        value = super(RespondentDetailView, self).lookup_field_value(context, obj, field)
        if field == "text" and obj.message:
            return obj.message.text

        return value

    def derive_title(self):
        return "Poll responses"

    def get_queryset(self):
        respondent = Respondent.objects.get(id=self.kwargs['pk'])
        self.extra_context['respondent'] = respondent
        self.extra_context['demo_polls'] = Poll.objects.filter(demographic=1)
        self.extra_context['demo_responses'] = PollResponse.objects.filter(respondent=respondent, poll__demographic=1)
        self.extra_context['question_responses'] = DemographicQuestionResponse.objects.filter(respondent=respondent)
        return PollResponse.objects.filter(respondent=respondent, poll__demographic=0)

class DemographicResponseForm(ModelForm):

    class Meta:
        model = PollResponse
    def __init__(self, *args, **kwargs):
        self.base_fields['category'].queryset = PollCategory.objects.filter(category_set = kwargs['instance'].poll.category_set)
        super(DemographicResponseForm, self).__init__(*args, **kwargs)

class DemographicUpdateView(SmartListUpdateView):
    model = PollResponse
    link_fields = ('poll',)
    fields = ('poll', 'category')
    update_fields = ('category',)
    form_class = DemographicResponseForm
    success_url = '/p/respondents/view/%(id)d/'
    link_url = "id@poll_view"
    permission = 'polls.respondent_update'

    template_name = "polls/demographic_update.html"

    def lookup_field_label(self, context, field, default=None):
        if field == "poll":
            return "Question"
        else:
            return "Answer"

    def lookup_field_value(self, context, obj, field):
        if field == "poll":
            return obj.poll.name
        return super(DemographicUpdateView, self).lookup_field_value(context, obj, field)

    def lookup_field_link(self, context, field, obj):
        return reverse("poll_catset_view", kwargs=dict(pk=obj.poll.category_set_id))

    def derive_title(self):
        return "Demographic Polls"

    def get_success_url(self):
        return '/p/respondents/view/%s/' % self.kwargs['pk']

    def get_form(self, form_class):
        self.form = model_forms.modelformset_factory(
            self.model,
            fields=self.update_fields,
            extra=0,
            formfield_callback=self.formfield_options, form=DemographicResponseForm)
        return self.form

    def get_context_data(self, **kwargs):
        context = super(DemographicUpdateView, self).get_context_data(**kwargs)
        questions = DemographicQuestion.objects.all().order_by('-priority')
        respondent = Respondent.objects.get(id=self.kwargs['pk'])

        # attach a response to the question if we have one
        for question in questions:
            responses = DemographicQuestionResponse.objects.filter(question=question, respondent=respondent)
            if responses:
                question.response = responses[0]

        context['questions'] = questions
        return context


    def get_queryset(self):
        respondent = Respondent.objects.get(id=self.kwargs['pk'])
        demo_polls = Poll.objects.filter(demographic=1)

        # make sure this respondent has a default response for each demo poll
        for poll in demo_polls:
            try:
                PollResponse.objects.get(respondent=respondent, poll=poll)
            except ObjectDoesNotExist:
                poll.responses.create(message=None, text='',
                                      category=None, secondary_category=None,
                                      respondent=respondent, active=True)


        return PollResponse.objects.filter(respondent=respondent, poll__demographic=1)

    def post(self, request, *args, **kwargs):
        form_class = self.get_form(self.get_form_class())
        self.form_post = form_class(request.POST)

        if self.form_post.is_valid():

            respondent = Respondent.objects.get(id=self.kwargs['pk'])

            # if we've a valid form, save off our free text responses
            questions = DemographicQuestion.objects.all().order_by('-priority')
            for question in questions:
                key = "question_%d" % question.pk
                if key in request.POST:

                    # we've got an answer, see if there is already a response
                    responses = DemographicQuestionResponse.objects.filter(respondent=respondent, question=question)
                    if responses:
                        if request.POST[key]:
                            responses[0].response = request.POST[key]
                            responses[0].save()
                        else:
                            responses[0].delete()
                    else:
                        if request.POST[key]:
                            DemographicQuestionResponse.objects.create(respondent=respondent, question=question, response=request.POST[key])

        # save our demographic poll responses
        return super(DemographicUpdateView, self).post(request, args, kwargs)

class PollChooserForm (forms.Form):
    other_polls = forms.ModelChoiceField(queryset=Poll.objects.all(), label="Add poll results for")

class BroadcastForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter'}), label='', required=True)
    password = forms.CharField(widget=forms.PasswordInput, required=True)

    def clean_password(self):
        password = self.cleaned_data['password']
        if password != 'YES':
            raise forms.ValidationError("That is the incorrect password, please contact your administrator for help")
        return password

class RespondentListView(SmartListView, ProcessFormView):
    model = Respondent
    template_name = 'polls/respondent_list.html'
    paginate_by = 50
    link_url = "id@respondent_view"
    permission = 'polls.respondent_list'

    def pre_process(self, request, *args, **kwargs):
        if 'number' in request.GET:
            number = request.GET['number']
            respondents = Respondent.objects.filter(identity=number)

            if respondents:
                return HttpResponseRedirect(reverse("respondent_view", args=[respondents[0].id]))

    def post(self, request, *args, **kwargs):

        # find out which form we are working with
        self.object_list = self.get_queryset()
        context = self.get_context_data(object_list=self.object_list)

        self.broadcast_form = BroadcastForm(request.POST)
        context['broadcast_form'] = self.broadcast_form

        if self.broadcast_form.is_valid():

            count = self.object_list.count()
            router = get_router()

            for respondent in self.object_list:
                connection = respondent.get_latest_connection()
                if connection:
                    outgoing = OutgoingMessage(connection, self.broadcast_form.cleaned_data['message'])
                    router.handle_outgoing(outgoing)

            messages.success(request, "%d user%s messaged" % (count, 's' if count != 1 else ''))

            # we need a new form since our send was successful
            context['broadcast_form'] = BroadcastForm()

        return self.render_to_response(context)


    def lookup_field_value(self, context, obj, field):
        value = super(RespondentListView, self).lookup_field_value(context, obj, field)
        if value is None:
            value = ""

        if field == "active" and value:
            value = '<div class="active_icon"></div>'
        elif not value:
            value = ''

        return value

    def get_queryset(self):
        broadcast_form = BroadcastForm()

        if 'message' in self.request.GET:
            broadcast_form.fields['message'].initial = self.request.GET['message']
            self.extra_context['message'] = self.request.GET['message']

        self.extra_context['broadcast_form'] = broadcast_form

        polls = []
        poll_ids = []

        if 'poll' in self.request.GET:
            poll_ids = self.request.GET.getlist('poll')
            polls = Poll.objects.filter(id__in=poll_ids)

        if 'sort' in self.request.GET:
            self.extra_context['sort'] = self.request.GET['sort']

        poll_spec = ""
        for poll in polls:
            poll.filters = list()
            poll_spec = "%s&poll=%s" % (poll_spec, poll.id)


        other_polls = Poll.objects.filter(~Q(id__in=poll_ids)).order_by("demographic")

        if len(other_polls) > 0:
            form = PollChooserForm()
            form.fields['other_polls'].queryset = other_polls
            self.extra_context['form'] = form

        self.extra_context['polls'] = polls
        self.extra_context['poll_spec'] = poll_spec

        regex = "poll(\d+)_cat(\d+):(.*)"

        if 'filter' in self.request.GET:
            filters = self.request.GET.getlist('filter')
            filter_spec = ""
            for f in filters:
                filter_spec = "%s&filter=%s" % (filter_spec, f)
                match = re.match(regex, f, re.IGNORECASE)
                if match:
                    poll_id = int(match.group(1))

                    poll = None
                    for p in polls:
                        if p.id == poll_id:
                            poll = p
                            break

                    if poll:
                        poll_filter = dict()
                        poll_filter['spec'] = f
                        poll_filter['value'] = match.group(3)
                        poll_filter['poll_id'] = poll.id
                        poll.filters.append(poll_filter)

            self.extra_context['filter'] = filter_spec
            self.extra_context['filters'] = filters

        return Respondent.get_queryset(polls, self.request.GET)

class PollListView(SmartListView):
    model = Poll
    fields = ('count', 'name', 'active', 'keywords', 'owner', 'created')
    template_name = 'polls/poll_list.html'
    link_fields = ('name',)
    search_fields = ('name__icontains','keywords__name__icontains')
    link_url = "id@poll_view"
    default_order = '-created'
    field_config = {
        'active': dict(label=''),
    }

    def derive_fields(self):
        if self.request.user.is_anonymous():
            return 'count', 'name', 'created'

        fields = super(PollListView, self).derive_fields()
        # if this user can create public polls, add a column
        if self.request.user.has_perm('polls.poll_public'):
            fields = list(fields)
            fields.append('is_public')
        return fields

    def get_is_public(self, obj):
        if obj.is_public:
            return "<div class='public'></div>"
        return "<div class='private'></div>"

    def get_keywords(self, obj):
        return "<nobr>%s</nobr>" % obj.get_keywords()

    def add_button(self):
        return self.request.user.has_perm('polls.poll_create')

    def get_owner(self, obj):
        return obj.user.username
    get_owner.verbose_name = "Owners"

    def get_active(self, obj):
        if obj.active():
            return '<div class="active_icon"></div>'
        else:
            return ''

    def get_queryset(self):
        queryset = super(PollListView, self).get_queryset()
        queryset = queryset.filter(demographic=False)

        # admins and editors can see all polls for their backends
        if self.request.user.has_perm('polls.poll_all'):
            user_backends = [_.backend.id for _ in self.request.user.backends.all()]
            queryset = queryset.filter(Q(user=self.request.user.id)|Q(backend__in=user_backends))

        # others can see non public polls for their backend or user
        elif self.request.user.has_perm('polls.poll_list'):
            user_backends = [_.backend.id for _ in self.request.user.backends.all()]
            queryset = queryset.filter(Q(user=self.request.user.id)|Q(backend__in=user_backends))

        # finally, others can only see public polls
        else:
            queryset = queryset.filter(is_public=True)

        return queryset

class DemographicPollListView(PollListView):
    fields = ('name', 'created')

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(DemographicPollListView, self).has_permission(request, *args, **kwargs)
        return request.user.has_perm('polls.poll_demographic')

    def derive_title(self):
        return "Demographic Polls"

    def lookup_field_link(self, context, field, obj):
        return reverse("poll_view", kwargs=dict(pk=obj.id))

    def get_queryset(self):
        queryset = super(PollListView, self).get_queryset()
        return queryset.filter(demographic=True)

class CategorizationForm(forms.Form):
    category = forms.ModelChoiceField(queryset=PollCategory.objects.all(), required=False, label="Move responses to")
    add_rules = forms.BooleanField(required=False, label="Add the following rules to category")
    update_rules = forms.CharField(widget=forms.Textarea, label="", required=False)
    secondary_category = forms.ModelChoiceField(queryset=PollCategory.objects.all(), required=False, label="Secondary")


class CategorizationCategoryCreateForm(ModelForm):
    class Meta:
        model = PollCategory
        exclude = ('poll', 'latitude', 'longitude', 'category_set')

    message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter'}),
                              required=False)
    new_rules = forms.CharField(widget=forms.Textarea(attrs=dict(cols=60, rows=6)),
                                help_text="What words will cause a response to be put in this category.  "
                                          "Messages must contain all the words on a line.",
                                required=False,
                                label="Rules")


class ResponseCategorizationView(SmartListView, ProcessFormView):
    template_name = "polls/response_categorization.html"
    paginate_by = 15

    def has_permission(self, request, *args, **kwargs):
        super(ResponseCategorizationView, self).has_permission(request, *args, **kwargs)
        poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
        return can_edit_poll(request.user, poll)

    def derive_title(self):
        pass

    def update_category(self, category, secondary_category, responses, new_rules):

        # put the responses into that category
        for response in responses:
            pr = PollResponse.objects.get(id=response)
            pr.category = category
            pr.secondary_category = secondary_category
            pr.save()

        # our category could be None
        if category and new_rules:
            old_rules = category.get_rules().split('\n')

            for rule in new_rules:
                if rule not in old_rules:
                    old_rules.append(rule)

            category.set_rules("\n".join(old_rules))
            category.save()

            # see if our new category rules match unknown responses
            unknowns = PollResponse.objects.filter(poll=category.category_set.poll, category=None)
            for unknown in unknowns:
                if category.matches_message(unknown.text, False):
                    unknown.category = category
                    unknown.save()
                # check if our fuzzy matches, maybe we should keep this literal instead?
                elif category.matches_message(unknown.text, True):
                    unknown.category = category
                    unknown.save()

        current_category = None
        if self.kwargs['category_id'] != '_':
            current_category = PollCategory.objects.get(id=self.kwargs['category_id'])

        if len(PollResponse.objects.filter(category=current_category)) > 0:
            return HttpResponseRedirect(reverse("response_categorization", kwargs=self.kwargs))
        else:
            return HttpResponseRedirect(reverse("poll_view", args=[self.kwargs['poll_id']]))


    def post(self, request, *args, **kwargs):

        # find out which form we are working with
        if request.POST['form'] == "categorization":
            self.categorization_form = CategorizationForm(request.POST)

            if self.categorization_form.is_valid():

                category = self.categorization_form.cleaned_data['category']
                responses = request.POST.getlist("responses")

                new_rules = None

                if 'add_rules' in request.POST and request.POST['add_rules'] == 'on':
                    new_rules = self.categorization_form.cleaned_data['update_rules'].split('\n')

                secondary_category = None
                if 'secondary_category' in self.categorization_form.cleaned_data:
                    secondary_category = self.categorization_form.cleaned_data['secondary_category']

                return self.update_category(category, secondary_category, responses, new_rules)

            else:
                import pdb; pdb.set_trace()

        elif request.POST['form'] == "new_category":
            self.category_form = CategorizationCategoryCreateForm(request.POST)

            if self.category_form.is_valid():

                # create our new category
                poll = Poll.objects.get(id=kwargs['poll_id'])
                category = self.category_form.save(commit=False)
                category.category_set = poll.category_set
                category.save()

                # now update the rules and responses for it
                responses = request.POST.getlist("responses")
                new_rules = self.category_form.cleaned_data['new_rules'].split('\n')

                secondary_category = None
                if 'secondary_category' in self.category_form.cleaned_data:
                    secondary_category = self.category_form.cleaned_data['secondary_category']

                return self.update_category(category, secondary_category, responses, new_rules)

            else:
                self.object_list = self.get_queryset()
                context = self.get_context_data(object_list=self.object_list)
                context['category_form'] = self.category_form
                context['show_create'] = True
                context['checked'] = request.POST.getlist("responses")
                return self.render_to_response(context)


    def get_context_data(self, **kwargs):
        poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
        context = super(ResponseCategorizationView, self).get_context_data(**kwargs)
        form = CategorizationForm()
        form.fields['category'].queryset = PollCategory.objects.filter(category_set=poll.category_set)
        form.fields['category'].initial = self.kwargs['category_id']
        form.fields['secondary_category'].queryset = PollCategory.objects.filter(category_set=poll.secondary_category_set)

        if not poll.secondary_category_set:
            del form.fields['secondary_category']

        context['categorization_form'] = form
        context['category_form'] = CategorizationCategoryCreateForm()
        return context


    def get_queryset(self):
        responses = PollResponse.objects.all()

        if 'poll_id' in self.kwargs:
            poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
            self.extra_context['poll'] = poll
            self.extra_context['categories'] = poll.category_set.categories.all()
            responses = responses.filter(poll=poll)

        if 'category_id' in self.kwargs:
            category_id = self.kwargs['category_id']

            # _ as an id means show uncategorized
            if category_id == '_':
                responses = responses.filter(category=None)
                self.extra_context['category'] = '_'
            else:
                category = get_object_or_404(PollCategory, id=self.kwargs['category_id'])
                self.extra_context['category'] = category
                responses = responses.filter(category=category)

        return responses

class PollResponseListView(SmartListView):
    model = PollResponse
    fields = ('number', 'text', 'category', 'created')
    template_name = 'polls/response_list.html'
    link_fields = ()

    def derive_fields(self):
        poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
        fields = self.fields
        if poll.secondary_category_set:
            fields = list(fields)
            fields.insert(3,'secondary_category')

        return fields

    def derive_title(self):
        if 'category_id' in self.kwargs and self.kwargs['category_id'] != "_":
            return "%s responses" % PollCategory.objects.get(id=self.kwargs['category_id'])
        return "Unknown responses"

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(PollResponseListView, self).has_permission(request, *args, **kwargs)
        poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
        return can_view_poll(request.user, poll)

    def get_queryset(self):
        responses = PollResponse.objects.all()

        if 'poll_id' in self.kwargs:
            poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
            self.extra_context['poll'] = poll
            responses = responses.filter(poll=poll)

        if 'category_id' in self.kwargs:
            category_id = self.kwargs['category_id']

            # _ as an id means show uncategorized
            if category_id == '_':
                responses = responses.filter(category=None)
                self.extra_context['category'] = '_'
            else:
                category = get_object_or_404(PollCategory, id=self.kwargs['category_id'])
                self.extra_context['category'] = category
                responses = responses.filter(category=category)

        return responses

    def get_field_filter(self, field):
        """
        Filter our categories for only our poll
        """
        poll = None
        if 'poll_id' in self.kwargs:
            poll = get_object_or_404(Poll, id=self.kwargs['poll_id'])
            self.extra_context['poll'] = poll

        if poll and field.name == 'category':
            return PollCategory.objects.filter(poll=poll)

        return None

    def get_number(self, obj):
        if self.request.user.has_perm('rapidsms_httprouter.view_message'):
            return obj.message.connection.identity
        else:
            str_len = len(obj.message.connection.identity)
            return "#" * (str_len - 4) + obj.message.connection.identity[-4:]

class PollDetailView(SmartReadView):
    model = Poll
    fields = ('name', 'description')
    template_name = 'polls/poll_detail.html'
    permission = "polls.poll_read"

    def has_permission(self, request, *args, **kwargs):
        super(PollDetailView, self).has_permission(request, *args, **kwargs)
        return can_view_poll(request.user, self.get_object())

    def as_json(self, context):
        """
        Responsible for turning our context into a dict that will be serialized to json
        """
        json = dict()
        poll = context['object']

        json['name'] = poll.name
        json['count'] = poll.count()
        json['unknown_count'] = poll.unknown_count()
        json['response_counts'] = poll.response_counts()
        json['active'] = poll.active()

        if poll.secondary_category_set:
            secondaries = []
            for secondary in poll.secondary_category_set.categories.all():
                secondaries.append(dict(id=secondary.id, name=secondary.name))
            json['secondary_categories'] = secondaries

        categories = []
        for category in poll.categories.all():
            cat = dict(name=category.name, id=category.id, count=category.count())

            if poll.secondary_category_set:
                cat['secondary_counts'] = category.get_secondary_counts()

            if category.latitude and category.longitude:
                cat['location'] = dict(lat=str(category.latitude),
                                       lng=str(category.longitude))

            categories.append(cat)

        json['categories'] = sorted(categories, key=lambda cat: cat['count'], reverse=True)

        responses = []
        for response in poll.responses.all().order_by('-created')[:10]:

            category = None
            secondary_category = None

            if response.category:
                category = response.category.name

            if response.secondary_category:
                secondary_category = response.secondary_category.name

            response = dict(number=response.respondent.identity,
                            category=category,
                            secondary=secondary_category,
                            text=response.message.text if response.message else "",
                            sent=response.created.strftime('%b %d %Y %H:%M %p'))

            responses.append(response)

        json['responses'] = responses

        return json

class PollIFrameView(PollDetailView):
    model = Poll
    fields = ('name', 'description')
    template_name = 'polls/poll_iframe.html'
    permission = "polls.poll_iframe"

    def get_context_data(self, **kwargs):
        context_data = super(PollIFrameView, self).get_context_data(**kwargs)
        context_data['graph_width'] = int(self.request.REQUEST.get('width', 500)) - 10

        # calculate our height based on our polls # of categories
        if not self.object.secondary_category_set:
            context_data['graph_height'] = min(len(self.object.categories.all()) * 75, 450)
        else:
            context_data['graph_height'] = 450

        return context_data

class PollForm(ModelForm):
    keywords = forms.CharField(help_text="Keywords for this poll separated by spaces", required=False)
    message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter', 'limit':100 }))
    unknown_message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter'}))
    campaign = forms.ModelChoiceField(queryset=QuickBlock.objects.filter(quickblock_type__slug='campaign'), required=False,
                                      help_text="What campaign this poll is part of, if any")

    categories = forms.CharField(widget=forms.Textarea(attrs={'cols':60, 'rows':'5'}), required=False,
                                 help_text="The new categories, one per line in the format: 'Category Name: word1, word2, word3 word4'")
    secondary_categories = forms.CharField(widget=forms.Textarea(attrs={'cols':60, 'rows':'5'}), required=False,
                                           help_text="The new categories, one per line in the format: 'Category Name: word1, word2, word3 word4'")

    template = forms.ChoiceField(choices=[], label="Primary Template",
                                 help_text="The primary categories to use for this poll")
    secondary_template = forms.ChoiceField(choices=[], label="Secondary Template",
                                           help_text="The secondary categories to use for this poll")

    def __init__(self, *args, **kwargs):
        user = kwargs['user']
        del kwargs['user']
        super(PollForm, self).__init__(*args, **kwargs)

        if not user.is_superuser:
            self.fields['backend'].queryset = Backend.objects.filter(pk__in=[_.backend.id for _ in user.backends.all()])
        else:
            self.fields['backend'].queryset = Backend.objects.all()

        public_templates = PollCategorySet.objects.filter(poll=None, is_public=True)
        choices = [(_.id, _.name) for _ in public_templates]
        choices.insert(0, (-1, "---- New Category Set ----"))
        choices.insert(0, (0, "-----"))

        self.fields['template'].choices = choices
        self.fields['secondary_template'].choices = choices

    def clean_template_field(self, template_name, field_name):
        if template_name in self.cleaned_data:
            value = int(self.cleaned_data[template_name])
            if value == -1:
                return None

            self.cleaned_data[field_name] = None

            if value == 0:
                return None
            else:
                return PollCategorySet.objects.get(id=value)

        return None

    def clean_template(self):
        return self.clean_template_field('template', 'categories')

    def clean_secondary_template(self):
        return self.clean_template_field('secondary_template', 'secondary_categories')

    class Meta:
        model = Poll
        exclude = ('started', 'ended', 'user', 'id', 'category_set', 'secondary_category_set')


class SettingsForm(ModelForm):
    class Meta:
        model = TracSettings

    trac_on_response = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter', 'limit':160}))
    trac_off_response = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter', 'limit':160}))
    recruitment_message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter', 'limit':60}))
    duplicate_message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter', 'limit':160}))

class TracSettingsCRUDL(SmartCRUDL):
    model = TracSettings
    actions = ('list', 'create', 'update')

    class Create(SmartCreateView):
        form_class = SettingsForm
        success_message = "Your settings have been saved."

    class Update(SmartUpdateView):
        form_class = SettingsForm
        success_message = "Your settings have been saved."

class PollUpdateView(SmartUpdateView):
    model = Poll
    form_class = PollForm
    success_url = "id@poll_view"
    fields = ('name', 'keywords', 'backend', 'description', 'message', 
              'unknown_message', 'started', 'ended', 'audio_file', 'detailed_chart', 'campaign')
    permission = "polls.poll_update"
    template_name = "polls/poll_update.html"
    delete_url = "id@poll_delete"

    field_config = {
        'started': dict(readonly=True),
        'ended': dict(readonly=True),
        'area_type' : dict(required=False)
    }

    def has_permission(self, request, *args, **kwargs):
        super(PollUpdateView, self).has_permission(request, *args, **kwargs)
        return can_edit_poll(request.user, self.get_object())

    def get_form_kwargs(self):
        kwargs = super(PollUpdateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_form(self, form_class):
        self.form = super(PollUpdateView, self).get_form(form_class)

        # if we are allowed, add option for making this template public
        if self.request.user.has_perm('polls.poll_public'):
            is_public = forms.BooleanField(label='Public', required=False)
            self.form.fields['is_public'] = is_public

            if self.fields:
                self.fields = list(self.fields) + ['is_public']

        return self.form

    def derive_fields(self):
        fields = super(PollUpdateView, self).derive_fields()

        if self.object.demographic:
            fields = ['name', 'keywords', 'description', 'message', 'unknown_message', 'always_update', 'started', 'ended']

        if not self.request.user.is_superuser and (self.request.user.backends.count() == 1 and "backend" in fields):
            fields.remove("backend")

        return fields

    def derive_initial(self):
        """
        Patch in our initial value for our keywords
        """
        self.initial = dict()
        self.initial['keywords'] = self.object.get_keywords()

        return self.initial

    def pre_save(self, obj):
        """
        Set our keywords using our method
        """
        if 'keywords' in self.form.cleaned_data:
            obj.set_keywords(self.form.cleaned_data['keywords'])

        # set our default backend if we aren't demographic
        if self.request.user.backends.count() == 1 and not self.object.demographic:
            obj.backend = self.request.user.backends.all()[0].backend

        return obj

class PollDeleteView(SmartDeleteView):
    model = Poll
    template_name = "smartmin/delete_confirm.html"
    permission = 'polls.poll_update'
    cancel_url = 'id@poll_edit'
    redirect_url = "/p/"

    def has_permission(self, request, *args, **kwargs):
        super(PollDeleteView, self).has_permission(request, *args, **kwargs)
        return can_edit_poll(request.user, self.get_object())

class PollCategoryForm(ModelForm):
    class Meta:
        model = PollCategory
        exclude = ('poll')

    message = forms.CharField(widget=forms.Textarea(attrs={'cols':'60', 'rows':'3', 'class':'char_counter'}),
                              required=False)
    rules = forms.CharField(widget=forms.Textarea(attrs=dict(cols=60, rows=6)),
                            help_text="What words will cause a response to be put in this category.  "
                                      "Messages must contain all the words on a line.",
                            required=False)

    latitude = forms.CharField(max_length=80, required=False)
    longitude = forms.CharField(max_length=80, required=False)

class PollCategoryCreateView(SmartCreateView):
    model = PollCategory
    form_class = PollCategoryForm
    fields = ('name', 'latitude', 'longitude', 'message', 'rules')
    permission = "polls.pollcategoryset_update"
    template_name = "polls/category_create.html"
    grant_permissions = ('polls.pollcategory_update',)
    javascript_submit = "submit"

    def get_parent_object(self):
        return PollCategorySet.objects.get(pk=self.kwargs['catset_id'])

    def get_success_url(self):
        category_set = PollCategorySet.objects.get(pk=self.kwargs['catset_id'])
        if category_set.poll:
            return reverse("poll_catset_view", args=[category_set.id])
        else:
            return reverse("catset_view", args=[category_set.id])

    def get_context_data(self, **kwargs):
        context = super(PollCategoryCreateView, self).get_context_data(**kwargs)
        context['pollcategoryset'] = PollCategorySet.objects.get(pk=self.kwargs['catset_id'])
        return context

    def pre_save(self, object):
        self.object = super(PollCategoryCreateView, self).pre_save(object)
        self.object.category_set = get_object_or_404(PollCategorySet, id=self.kwargs['catset_id'])
        self.object.set_rules(self.form.cleaned_data['rules'])
        return self.object

class PollCategoryUpdateView(SmartUpdateView):
    model = PollCategory
    form_class = PollCategoryForm
    fields = ('name', 'latitude', 'longitude', 'message', 'rules')
    permission = "polls.pollcategory_update"
    template_name = "polls/category_update.html"
    javascript_submit = "submit"

    def get_success_url(self):
        if self.object.category_set.poll:
            return reverse("poll_catset_view", args=[self.object.category_set.id])
        else:
            if "loc" in self.request.POST:
                return self.request.POST["loc"]
            return reverse("catset_view", args=[self.kwargs['catset_id']])

    def get_context_data(self, **kwargs):
        context = super(PollCategoryUpdateView, self).get_context_data(**kwargs)
        context['pollcategoryset'] = self.object.category_set
        context['delete_url'] = reverse('poll_category_delete', args=[self.object.category_set.id, self.object.id])
        return context

    def derive_initial(self):
        """
        Patch in our initial value for our rules
        """
        self.initial = dict()
        self.initial['rules'] = self.object.get_rules()
        return self.initial

    def form_invalid(self, form):
        return super(PollCategoryUpdateView, self).form_invalid(form)

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(PollCategoryUpdateView, self).has_permission(request, *args, **kwargs)
        if not has_perm:
            poll = self.get_object().category_set.poll
            if poll:
                has_perm = poll.user == self.request.user

        return has_perm

    def form_valid(self, form):
        """        
        Set our rules using our method
        """
        self.object = form.save(commit=False)
        self.object.set_rules(form.cleaned_data['rules'])
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class PollCategoryDeleteView(SmartDeleteView):
    model = PollCategory
    permission = 'polls.poll_update'
    cancel_url = 'id@catset_view'

    def get_template_names(self):
        # if it has a poll, then we warn for orphaned responses
        if self.get_object().category_set.poll:
            return "polls/category_delete_poll.html"
        else:
            return "polls/category_delete.html"

    def pre_delete(self, obj):
        category = self.get_object()
        if category.category_set.poll:

            # delete will kill all respones along with the category
            # if they don't want to delete respones, unassign them first
            if self.request.POST['responses'] != 'delete':
                for response in category.responses.all():
                    response.category = None
                    response.save()

    def get_redirect_url(self):
        if self.get_object().category_set.poll:
            return reverse("poll_catset_view", args=[self.get_object().category_set.id])
        else:
            if "loc" in self.request.POST:
                return self.request.POST["loc"]
            return reverse("catset_view", args=[self.kwargs['catset_id']])

    def get_cancel_url(self):
        if self.get_object().category_set.poll:
            return reverse("poll_catset_view", args=[self.get_object().category_set.id])
        else:
            if "loc" in self.request.POST:
                return self.request.POST["loc"]
            return reverse("catset_view", args=[self.kwargs['catset_id']])

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(PollCategoryDeleteView, self).has_permission(request, *args, **kwargs)
        if not has_perm:
            poll = self.get_object().poll
            has_perm = poll.user == self.request.user

        return has_perm

class PollCreateView(SmartCreateView):
    model = Poll
    form_class = PollForm
    success_url = "id@poll_view"
    fields = ('name', 'keywords', 'backend', 'description', 'message', 'unknown_message', 'template', 'categories', 'secondary_template', 'secondary_categories', 'detailed_chart', 'campaign')
    permission = "polls.poll_create"
    grant_permissions = ("polls.poll_read", "polls.poll_update")
    template_name = "polls/poll_create.html"

    def get_form_kwargs(self):
        kwargs = super(PollCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def derive_fields(self):
        fields = super(PollCreateView, self).derive_fields()

        if self.request.user.backends.count() == 1 and "backend" in fields:
            fields.remove("backend")

        return fields

    def get_form(self, form_class):
        self.form = super(PollCreateView, self).get_form(form_class)

        # if we are allowed, add option for making this template public
        if self.request.user.has_perm('polls.poll_public'):
            is_public = forms.BooleanField(label='Public', required=False)
            self.form.fields['is_public'] = is_public

            if self.fields:
                self.fields += ('is_public',)

        return self.form

    def pre_save(self, obj):
        """
        We overload before saving to tie the object to the current user
        """
        obj = super(PollCreateView, self).pre_save(obj)
        obj.user = self.request.user

        if 'keywords' in self.form.cleaned_data:
            obj.set_keywords(self.form.cleaned_data['keywords'])

        # set our backend appropriately
        if self.request.user.backends.count() == 1:
            obj.backend = self.request.user.backends.all()[0].backend

        return obj

    def post_save(self, obj):
        obj = super(PollCreateView, self).post_save(obj)

        if self.form.cleaned_data.get('categories', None):
            obj.category_set.create_categories_from_string(self.form.cleaned_data['categories'])

        if self.form.cleaned_data.get('secondary_categories', None):
            obj.secondary_category_set = obj.create_category_set(None)
            obj.secondary_category_set.create_categories_from_string(self.form.cleaned_data['secondary_categories'])
            obj.save()

        return obj

class DemographicPollForm(ModelForm):
    template = forms.ChoiceField(choices=[], label="Template",
                                 help_text="The categories to use for this poll")
    categories = forms.CharField(widget=forms.Textarea(attrs={'cols':60, 'rows':'5'}), required=False,
                                 help_text="The new categories, one per line in the format: 'Category Name: word1, word2, word3 word4'")

    def __init__(self, *args, **kwargs):
        del kwargs['user']
        super(DemographicPollForm, self).__init__(*args, **kwargs)

        public_templates = PollCategorySet.objects.filter(poll=None, is_public=True)
        choices = [(_.id, _.name) for _ in public_templates]
        choices.insert(0, (-1, "---- New Category Set ----"))
        choices.insert(0, (0, "-----"))

        self.fields['template'].choices = choices

    def clean_template(self):
        if 'template' in self.cleaned_data:
            value = int(self.cleaned_data['template'])
            if value == -1:
                return None

            self.cleaned_data['categories'] = None

            if value == 0:
                return None
            else:
                return value

        return None

    class Meta:
        model = Poll
        exclude = ('keyword', 'secondary_template', 'started', 'ended', 'user', 'id', 'category_set', 'secondary_category_set', 'unknown_message', 'message')

class DemographicPollCreateView(PollCreateView):
    form_class = DemographicPollForm
    fields = ('name', 'description', 'template', 'categories')

    def has_permission(self, request, *args, **kwargs):
        has_perm = super(DemographicPollCreateView, self).has_permission(request, *args, **kwargs)
        return request.user.has_perm('polls.poll_demographic')

    def derive_title(self):
        return "Create Demographic Poll"

    def get_context_data(self, *args, **kwargs):
        context_data = super(DemographicPollCreateView, self).get_context_data(*args, **kwargs)
        return context_data

    def pre_save(self, obj):
        obj = super(DemographicPollCreateView, self).pre_save(obj)
        obj.demographic = True
        obj.backend = None
        return obj


def poll_start(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if not can_edit_poll(request.user, poll):
        return HttpResponseRedirect(reverse('users.user_login'))

    # if this poll was already started, say so
    try:
        poll.start()
        messages.success(request, "Poll has been started.")
    except Exception as e:
        messages.error(request, unicode(e))

    return HttpResponseRedirect(reverse("poll_view", args=[poll_id,]))


def poll_stop(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)

    if not can_edit_poll(request.user, poll):
        return HttpResponseRedirect(reverse('users.user_login'))

    # if this poll was already started, say so
    try:
        poll.end()
        messages.success(request, "Poll has been ended.")
    except Exception as e:
        messages.error(request, unicode(e))

    return HttpResponseRedirect(reverse("poll_view", args=[poll_id,]))

