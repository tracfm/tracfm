import re
import time
import math

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Count
from django.core.urlresolvers import reverse
from django.dispatch import receiver

from locations.views import location_deleted
from guardian.shortcuts import assign
from guardian.core import ObjectPermissionChecker

from rapidsms.models import Backend
from rapidsms_httprouter.models import Message, Connection
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django_quickblocks.models import QuickBlock

from django.db.models import Q
import settings
from smartmin.models import SmartModel

class TracSettings(models.Model):
    backend = models.ForeignKey(Backend, null=True, blank=True, unique=True,
                                help_text="The backend these settings apply to, if not set then these are the defaults")
    trac_on_response = models.CharField(max_length=160)
    trac_off_response = models.CharField(max_length=160)
    trac_reset_response = models.CharField(max_length=160)
    recruitment_message = models.CharField(max_length=60)
    duplicate_message = models.CharField(max_length=160)

    @classmethod
    def get_setting(cls, backend, field):
        backend_settings = cls.settings(backend)
        setting = getattr(backend_settings, field, None)
        return setting

    @classmethod
    def settings(cls, backend):
        backend_settings = TracSettings.objects.filter(backend=backend)
        if backend_settings:
            return backend_settings[0]
        else:
            default = TracSettings.objects.filter(backend=None)
            if not default:
                return TracSettings.objects.create()
            else:
                return default[0]

class Poll(models.Model):
    """
    Represents a Poll.
    """
    name = models.CharField(max_length=128, help_text="The name of this poll, cannot be empty")
    description = models.TextField(help_text="A short description, including the goals of the poll.")
    message = models.CharField(max_length=100, help_text="The default SMS response which will be sent to users when they participate in this poll.")
    unknown_message = models.CharField(max_length=160, help_text="The SMS response which will be sent to users their message is not recognized.")
    started = models.DateTimeField(null=True, blank=True, verbose_name="Started")
    ended = models.DateTimeField(null=True, blank=True, verbose_name="Ended")

    # templates to base our primary and secondary categories off of
    template = models.ForeignKey('PollCategorySet', related_name="template", blank=True, null=True)
    secondary_template = models.ForeignKey('PollCategorySet', related_name='secondary_template', blank=True, null=True)

    # the cloned category set for the secondary template
    category_set = models.ForeignKey('PollCategorySet', related_name='category_set', blank=True, null=True)
    secondary_category_set = models.ForeignKey('PollCategorySet', related_name='secondary_category_set', blank=True, null=True)

    demographic = models.BooleanField(default=False)

    detailed_chart = models.BooleanField(default=False)

    # should this poll get processed against every incoming message
    always_update = models.BooleanField(default=False, help_text="Process this poll against every message")

    # a link to an MP3 audio recording for this poll
    audio_file = models.CharField(max_length=512, blank=True, null=True, help_text="Link to MP3 recording for the radio program")

    user = models.ForeignKey(User, verbose_name="Owner")

    is_public = models.BooleanField(default=False,
                                    help_text="Whether this poll is available for everyone to view")

    # what backend this message is working against
    backend = models.ForeignKey(Backend, null=True,
                                help_text="Which aggregator messages must come from in order to respond to this poll")

    campaign = models.ForeignKey(QuickBlock, null=True, related_name='polls',
                                 help_text="Which campaigns this poll is associated with")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __getattribute__(self, name):
        """ nicer accessor for categories """
        if name == "categories":
            return self.category_set.categories
        if name == "secondary_categories":
            return self.secondary_category_set.categories
        return super(Poll, self).__getattribute__(name)

    class Meta:
        ordering = ('-id',)

    def __unicode__(self):

        if self.demographic:
            return "* %s" % self.name

        return self.name

    def get_keywords(self):
        return " ".join([keyword.name for keyword in self.keywords.all()])

    def set_keywords(self, keywords):
        # these get dealt with on save
        self._keywords = keywords

    def save(self, *args, **kwargs):

        # only do this on the first save
        if not self.pk:

            # do the actual save
            super(Poll, self).save(*args, **kwargs)

            # create our primary category set
            self.category_set = self.create_category_set(self.template)

            if self.secondary_template:
                self.secondary_category_set = self.create_category_set(self.secondary_template)

            self.save()

        else:
            super(Poll, self).save(*args, **kwargs)

        # now also save our keywords
        keywords = getattr(self, '_keywords', None)
        if not keywords is None:

            # remove our existing keywords
            self.keywords.all().delete()

            # and set our new ones
            for keyword in keywords.split(' '):
                keyword = keyword.strip()
                if len(keyword) > 0:
                    self.keywords.create(name=keyword)


    def create_category_set(self, template):
        category_set = PollCategorySet.objects.create(poll=self, user=self.user)
        assign('polls.pollcategoryset_read', self.user, category_set)
        assign('polls.pollcategoryset_update', self.user, category_set)

        if template:
            for category in template.categories.all():
                new_category = category_set.categories.create(name=category.name,
                                                          message=category.message,
                                                          latitude=category.latitude,
                                                          longitude=category.longitude)
                new_category.set_rules(category.get_rules())
                new_category.save()
                assign('polls.pollcategory_update', self.user, new_category)

        return category_set

    def has_locations(self):
        for category in self.categories.all():
            if category.latitude and category.longitude:
                return True
        return False
    
    def tick_interval(self):
        """
        Returns the tick interval for a chart, based on the length of our chart
        """
        # not started?  nothing to see
        if not self.started:
            return 3600000

        started = self.started

        # not ended, use current date
        ended = self.ended
        if not ended:
            ended = datetime.now()

        # by default we group by day
        interval = 3600 * 24 * 1000

        # but if we've only run for a few days, then use hours
        if ended - started < timedelta(days=1):
            interval = 3600 * 1000 * 5

        return interval

    def response_counts(self):
        """
        Returns a list of dict objects, containing the date and the number of responses sent in.
        """
        # not started?  nothing to see
        if not self.started:
            return None

        started = self.started

        # not ended, use current date
        ended = self.ended
        if not ended:
            ended = datetime.now()

        # by default we group by day
        increment = timedelta(days=1)

        # but if we've only run for a few days, then use hours
        if ended - started < timedelta(days=1):
            increment = timedelta(hours=1)

            if ended - started < timedelta(hours=12):
                started = ended - timedelta(hours=12)
            
            started = started.replace(minute=0, second=0, microsecond=0)
        else:
            started = started.replace(hour=0, second=0, microsecond=0)

        # not very long, move our end date forward
        if ended - started < increment * 6:
            ended = started + increment * 6

        # ok, now let's create our timeline, which has a pair of date, count object
        timeline = []

        current = started
        while current < ended:
            count = PollResponse.objects.filter(poll=self, created__gte=current,
                                                created__lt=current+increment).count()

            epoch = time.mktime(current.timetuple()) * 1000
            timeline.append(dict(time=int(epoch), value=count))
            current += increment

        return timeline

    def count(self):
        """
        Returns the number of responses this has
        """
        return self.responses.all().count()

    def unknown_count(self):
        """
        Returns the number of unknown responses we have
        """
        return self.responses.filter(category=None).count()

    def clean(self):
        """
        Cleans our model instance before saving.  All we really do is strip our keyword of whitespace and lowercase it.
        """
        return super(Poll, self).clean()

    def active(self):
        """
        Whether this poll is currently active or not.
        """
        now = datetime.now()
        return bool(self.started and self.started < now and not self.ended)

    def start(self):
        """
        Starts a poll, possibly throwing an error if there is one.
        """
        if self.started:
            raise Exception("Poll has already been started and is active.")
        
        if self.ended:
            raise Exception("Poll cannot be started, it is already complete.")

        # check whether there are any other polls that could be run
        for active_poll in Poll.objects.filter(ended=None, backend=self.backend).exclude(started=None):
            if self.keywords.count():
                for keyword in self.keywords.all():
                    for active_keyword in active_poll.keywords.all():
                        if active_keyword.name == keyword.name:
                            raise Exception("Another poll is already active.  You must end the '%s' poll before making this one active." % active_poll.name)
            else:
                if not active_poll.keywords.count():
                    raise Exception("Another poll is already active.  You must end the '%s' poll before making this one active." % active_poll.name)


        self.started = datetime.now()
        self.save()

    def end(self):
        """
        Ends a poll, possibly throwing an error if there is one.
        """
        if not self.started:
            raise Exception("Poll is not active and cannot be ended.")

        if self.ended:
            raise Exception("Poll has already been ended.")

        self.ended = datetime.now()
        self.save()

        # Wouter requests this feature be deactivated for the time being
        # on August 8th, 2011. Losing active users too quickly in practice.
        # Respondent.deactivate_users()


    def has_empty_categories(self):
        for cat in self.category_set.categories.all():
            if cat.responses.count() == 0:
                return True
        return False

    def find_category(self, message, categories, fuzzy=True):
        """
        Given message contents, tries to find the category that it matches.

        If no category is found, then None is returned
        """
        # first pass, no fuzzy
        for category in categories.all():
            if category.matches_message(message):
                return category

        # second pass, fuzzy
        if fuzzy:
            for category in categories.all():
                if category.matches_message(message, True):
                    return category

        return None

    def clear_response(self, message):
        """
        Marks any previous response for this poll as inactive. Used on 'trac reset' to clear
        poll updates that are marked as 'always_update'
        """
        # gate this for demographic polls only as a safety check
        if self.demographic:
            respondent = Respondent.get_respondent(message)
            # mark all prev responses as inactive
            prev_responses = PollResponse.all.filter(respondent=respondent, poll=self)
            for prev_response in prev_responses:
                prev_response.active = False
                prev_response.save()

    def update_response(self, message):
        """
        Finds any previous response and updates it with this message. This is to support polls with the
        'always_update' flag for demographic polls.
        """
        # gate this for demographic polls only as a safety check
        if self.demographic:

            respondent = Respondent.get_respondent(message)

            # see if we've got a match, using the entire message including keyword
            # for auto updating, we don't want to use fuzzy matching as that could overreach easily
            category = self.find_category(message.text, self.categories, fuzzy=False)

            if category:
                # demo polls should only have at most one response
                prev_responses = PollResponse.objects.filter(respondent=respondent, poll=self, active=True).exclude(category=None).order_by("id")

                # don't add unless there's not responses yet
                if not len(prev_responses):
                    self.process_message(message, ignore_limit=True)

    def process_message(self, message, ignore_limit=False):
        """
        Processes an incoming SMS message.  We create a response object and try to classify the response
        in one of our categories.
        """
        # text of our message
        text = message.text
        
        # strip off a keyword if there is one
        for keyword in self.keywords.all():
            parts = trim_keyword(text, keyword=keyword.name)
            if parts and len(parts) == 2:
                (kw, text) = parts

        # see if we can figure out what category this falls in
        category = self.find_category(text, self.categories)

        # if there's a secondary category set, process those too
        # but only if there was a primary category found
        secondary_category = None
        if category and self.secondary_category_set:
            secondary_category = self.find_category(text, self.secondary_categories)
            # we don't allow primary matches without secondary matches
            if not secondary_category:
                category = None

        respondent = Respondent.get_respondent(message)
        prev_responses = PollResponse.all.filter(respondent=respondent, poll=self).exclude(category=None)

        if len(prev_responses) > 0:
            if ignore_limit or len(prev_responses) == 1:
                response = self.responses.create(message=message, text=text,
                                         category=category, secondary_category=secondary_category,
                                         respondent=respondent, active=ignore_limit)
            else:
                # if two messages are already there, it's time to ignore them
                return None

        else:
            # make all previously unknown message inactive
            prev_unknown = PollResponse.all.filter(respondent=respondent, poll=self, category=None)
            for unknown in prev_unknown:
                unknown.active = False
                unknown.save()

            response = self.responses.create(message=message, text=text,
                                         category=category, secondary_category=secondary_category,
                                         respondent=respondent)

            respondent.last_response = response
            respondent.save()

        # return our response object
        return response

    @classmethod
    def find_poll(cls, text, backend):
        """
        Finds the poll that is appropriate for the passed in text.

        We search in the following order:
          1. Strip the first word off, see if it is an exact match for any of our active polls
          2. Go through the same list, but see if the keyword is within an edit distance of 1
          3. Return the default (no keyword) poll if there is one
        """
        # we first try to match those polls that have keywords
        keyword = trim_keyword(text)
        for poll in Poll.objects.filter(ended=None, backend=backend).exclude(started=None).order_by('id'):
            for poll_keyword in poll.keywords.all():
                if keyword and keyword[0].lower() == poll_keyword.name.lower():
                    return poll

        # on the second pass we use edit distance
        for poll in Poll.objects.filter(ended=None, backend=backend).exclude(started=None).order_by('id'):
            for poll_keyword in poll.keywords.all():
                if keyword and edit_distance(keyword[0], poll_keyword.name.lower()) <= 1:
                    return poll

        # finally return a catch all poll if there is one
        for poll in Poll.objects.filter(ended=None, backend=backend).exclude(started=None).order_by('id'):
            if not poll.keywords.count():
                return poll

        return None

class PollKeyword(models.Model):
    """
    A keyword option for a given poll, they can have more than one
    """
    name = models.CharField(max_length=32, help_text="The keyword to use for a poll")
    poll = models.ForeignKey(Poll, related_name="keywords")

    def __unicode__(self):
        return self.name

class PollCategorySet(models.Model):
    """
    Represents a set of categories that can be used as a template for categories
    """
    name = models.CharField(max_length=80, help_text="A short name describing the categories in this set")
    description = models.TextField(help_text="A short description describing what this set of categories are useful for.")

    # if a category set doesn't belong to a poll, then it's a template
    poll = models.ForeignKey(Poll, blank=True, null=True)
    user = models.ForeignKey(User, verbose_name="Owner")

    # is this poll public
    is_public = models.BooleanField(default=False,
                                    help_text="Whether this template will show up in the poll creation form")

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = "templates"
        verbose_name = "template"
        permissions = (
            ('pollcategoryset_public', 'Creates public templates'),
        )

    @classmethod
    def parse_category_string(cls, category_def):
        """
        Tries to parse the passed in string into categories.
        """
        categories = []
        for line in category_def.splitlines():
            line = line.strip()
            category_name = line
            matches = []

            colon_index = line.rfind(':')

            if colon_index != -1:
                category_name = line[:colon_index]
                rest = line[colon_index+1:]
                matches = [_.strip() for _ in rest.split(',')]

            categories.append((category_name, matches))
        
        return categories

    def get_empty_categories(self):
        return self.categories.annotate(count=Count("primary_responses")).filter(count=0)

    def create_categories_from_string(self, category_string):
        categories = PollCategorySet.parse_category_string(category_string)

        for (category_name, rules) in categories:
            new_category = self.categories.create(name=category_name)
            new_category.set_rules("\n".join(rules))
            new_category.save()

    def create_categories(self, poll):
        # clone all the categories from the provided poll
        if poll:
            for category in poll.categories.all():
                new_category = self.categories.create(name=category.name,
                                                      message=category.message,
                                                      latitude=category.latitude,
                                                      longitude=category.longitude)
                new_category.set_rules(category.get_rules())
                new_category.save()


class PollCategory(models.Model):
    """
    Represents a category a poll can land in.
    """
    name = models.CharField(max_length=80, help_text="A short name for this category, this will be used in graphs and reports.")
    message = models.CharField(max_length=100, help_text="The SMS response that will be sent to recipients who's answer matches this category.  If empty, the default poll response will be used.")

    # categories must belong to a set
    category_set = models.ForeignKey(PollCategorySet, related_name="categories")

    # optionally categories can have a location
    latitude = models.CharField(max_length=80)
    longitude = models.CharField(max_length=80)

    #def delete(self, using=None):
    #    print "Deleting pollcategory %s" % self
    #    for response in self.responses.all():
    #        response.delete()
    #
    #    super(PollCategory, self).delete(using=using)

    def __init__(self, *args, **kwargs):
        self._rules = None
        super(PollCategory, self).__init__(*args, **kwargs)

    class Meta:
        unique_together = (('name', 'category_set'))
        verbose_name_plural = "categories"
        verbose_name = "category"

    def __getattribute__(self, name):
        """ nicer accessor for categories """
        if name == "responses":
            return PollResponse.objects.filter(Q(category=self.pk)|Q(secondary_category=self.pk))
        return super(PollCategory, self).__getattribute__(name)

    def get_secondary_counts(self):
        """ Get a dictionary of metrics for responses in the secondary categories """
        total = self.responses.count()
        secondaries = self.category_set.poll.secondary_categories.all()
        secondary_counts = {}
        for secondary in secondaries:
            count = PollResponse.objects.filter(category=self, secondary_category=secondary).count()
            
            # a human friendly percentage with tenths precision
            pct = 0
            if total > 0:
                pct = math.floor(1000  * (float(count) / float(total))) / 10

            secondary_counts[secondary.id] = dict(name=secondary.name, count=count, pct=pct)
        return secondary_counts


    def location(self):
        if self.latitude and self.longitude:
            return "%s, %s" % (self.latitude, self.longitude)
        return None

    @receiver(location_deleted)
    def detach_location(sender, **kwargs):
        """ A location was deleted, see if we should detach ourselves from it """

        if not kwargs['delete_deep']:
            for category in PollCategory.objects.filter(area=kwargs['location']):
                category.area = None
                category.save()

    def get_absolute_url(self):
        """
        Categories are viewed in the context of their poll
        """
        return reverse('poll_view', args=[self.poll.id])
    
    def set_rules(self, rules):
        """
        Sets the rules that should be created for this poll category after it is saved.  Note that these
        are only written when the object's save() method is called.
        """
        self._rules = rules

    def get_rules(self):
        """
        Returns our rules as a list of strings, delimited by '\n'
        """
        return "\n".join([rule.match for rule in self.rules.all()])

    def get_rule_list(self):
        """
        Returns our rules as a comma separated list
        """
        return ", ".join([rule.match for rule in self.rules.all()])

    def count(self):
        """
        Returns how many responses we have in this category
        """
        return self.responses.all().count()

    def matches_message(self, message, fuzzy=False):
        """
        Returns whether this message matches this category.
        """
        # first check our rules
        for rule in self.rules.order_by('order'):
            if rule.matches(message, fuzzy):
                return True

        return False

    def save(self, **kwargs):
        """
        We overload our save to set/update any rules after we are committed.
        """
        # save away
        super(PollCategory, self).save(**kwargs)

        # now also save our rules if they are present
        rules = getattr(self, '_rules', None)
        if not rules is None:
            
            # remove our existing rules
            self.rules.all().delete()

            # and set our new ones
            for rule in rules.splitlines():
                if len(rule.strip()) > 0:
                    match = re.search("^#(-?\d+)?(:)?(-?\d+)?$", rule.strip())
                    if match:
                        # is a range query
                        if match.group(2):
                            self.rules.create(match=rule.strip(), numeric=True, lower_bound=match.group(1), upper_bound=match.group(3))
                        # an exact match
                        else:
                            self.rules.create(match=rule.strip(), lower_bound=match.group(1), upper_bound=match.group(1), numeric=True)

                    else:
                        self.rules.create(match=rule.strip())

    def __unicode__(self):
        return self.name

class PollRule(models.Model):
    """
    Represents a rule for a category.
    """
    category = models.ForeignKey(PollCategory, related_name='rules')
    match = models.CharField(max_length=64)
    order = models.IntegerField(default=0)
    numeric = models.BooleanField(default=False)
    lower_bound = models.IntegerField(null=True)
    upper_bound = models.IntegerField(null=True)

    def save(self, **kwargs):
        """
        We lowercase our match strings.
        """
        self.match = self.match.lower()
        if not self.numeric:
            self.match = re.sub("[^0-9a-z]", " ", self.match)
        super(PollRule, self).save(**kwargs)

    def in_numeric_range(self, message, fuzzy):

        pattern = "$(-?\d+)^"
        if fuzzy:
            pattern = "(-?\d+)"

        match = re.search(pattern, message)
        if match:
            message_value = match.group(1)

            # check upper and lower boundaries
            message_value = int(message_value)

            if self.lower_bound and message_value < self.lower_bound:
                return False

            if self.upper_bound and message_value > self.upper_bound:
                return False

            return True

        return False
    
    def matches(self, message, fuzzy=False):
        """
        Returns whether this rule matches the passed in message.  The 'fuzzy' attribute
        marks whether any edit distance will be taken into account when matching
        """

        if self.numeric:
            return self.in_numeric_range(message, fuzzy)
        else:

            raw = message.lower()
            raw = re.sub("[^0-9a-z]", " ", raw)
            raw = raw.split()

            matches = self.match.lower()
            matches = re.sub("[^0-9a-z]", " ", matches)
            matches = matches.split()

            # see if each of our matches is present
            scores = [match in raw for match in matches]

            # we need to match all our matches
            matched = not False in scores

            # if we are doing fuzzy, try that
            if not matched and fuzzy:
                scores = []
                for match in matches:
                    match_scores = [edit_distance(word, match) <= 1 for word in raw]
                    scores.append(True in match_scores)
                matched = not False in scores

            return matched

    class Meta:
        ordering = ('order', '-category')

class ActiveManager(models.Manager):
    """
    A manager that only selects items which are still active.
    """
    def get_query_set(self):
        """
        Where the magic happens, we automatically throw on an extra active = True to every filter
        """
        return super(ActiveManager, self).get_query_set().filter(active=True)


class Respondent(models.Model):
    """
    Represents a unique respondent in the system. Respondents may have responded
    to more than one poll and this is a representation of that person.
    """
    name = models.CharField(max_length=100)
    notes = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    active_date = models.DateTimeField(null=True)
    last_response = models.ForeignKey('PollResponse', related_name="last_respondent", null=True)
    identity = models.CharField(max_length=100, null=True, db_index=True)

    def get_latest_connection(self):
        # this is going to give us the last connection created for that identity
        # not necessarily the last one that was used
        connections = Connection.objects.filter(identity=self.identity).order_by('-id')
        if len(connections) > 0:
            return connections[0]

    def get_active_flag(self, message):
        """
        Determines if the given message is intended to flip active flag.
        Returns 'on', 'off', or None
        """
        regex = "^\s*(trac|track)\s*(on|off|reset)\s*$"

        # do we match?
        match = re.match(regex, message.text, re.IGNORECASE)

        # if so, return the rest of the message
        if match:
            return match.group(2).lower().strip()

        return None

    def set_active_status(self, active):
        """
        Sets the active flag for this user. If it's changed, returns True
        otherwise returns False
        """
        if active:
            if not self.active:
                self.active = True
                self.active_date = datetime.utcnow()
                self.save()
                return True
        else:
            if self.active:
                self.active = False
                self.save()
                return True
        return False

    @classmethod
    def deactivate_users(cls):
        # find the poll that ended three polls ago
        polls = Poll.objects.filter(demographic=False).order_by('-ended')[:3]

        if polls.count() >= 3:
            old_poll = polls[2]
            if old_poll.ended:

                # users that haven't responded to anything yet
                users = Respondent.objects.filter(active=True, last_response=None, active_date__lt=old_poll.started)
                for user in users:
                    user.active = False
                    user.save()

                # users that haven't responded in a while
                users = Respondent.objects.filter(active=True, last_response__created__lt=old_poll.started, active_date__lt=old_poll.started)
                for user in users:
                    user.active = False
                    user.save()

                    
    @classmethod
    def get_respondent(cls, message):
        # see if we need to create our respondent
        respondent = None
        try:
            respondent = Respondent.objects.get(identity=message.connection.identity)
        except ObjectDoesNotExist:
            respondent = Respondent.objects.create(identity=message.connection.identity)
        return respondent

    @classmethod
    def get_queryset(cls, polls, params):

        sql = "FROM (SELECT respondent.* "

        agg_template = ", MAX(IF (response.poll_id=%(poll_id)d, cat%(cat)d.name, '--')) AS poll%(poll_id)d_cat%(cat)d "
        for poll in polls:
            sql += agg_template % dict(poll_id=poll.id, cat=1)
            sql += agg_template % dict(poll_id=poll.id, cat=2)

        sql += " FROM polls_respondent respondent"

        if polls:
            sql += ", polls_pollresponse response"
            sql += " LEFT JOIN polls_pollcategory cat1	ON response.category_id = cat1.id "
            sql += " LEFT JOIN polls_pollcategory cat2	ON response.secondary_category_id = cat2.id "

            sql += " WHERE	response.poll_id IN ("
            delim = ""
            for poll in polls:
                sql = sql + delim + str(poll.id)
                delim = ","

            sql += ") AND "
            sql += " respondent.id = response.respondent_id GROUP BY respondent_id "

        sql += ") flattened "

        if 'filter' in params:
            filters = params.getlist('filter')
            delim = " "
            sql += " WHERE "
            for f in filters:
                f = f.split(":", 1)
                if len(f) == 2:
                    field = f[0]
                    value = f[1]
                    sql = sql + delim + field + "='" + value + "' "
                    delim = " AND "

        if 'sort' in params:
            sort = str(params['sort'])
            if len(sort) > 0:
                if sort.startswith("-"):
                    sql = sql + " ORDER BY " + sort[1:] + " desc"
                else:
                    sql = sql + " ORDER BY " + sort
        else:
            sql += " ORDER BY id desc"

        # print sql
        # holy sql-injection batman! This is gated by admin, but this
        # should still be made a lot safer by using params for raw queries.
        try:
            queryset = Respondent.objects.raw("SELECT * " + sql)

            # RawQuerySet has no len() support, patch in count for pagination
            cursor = connection.cursor()
            cursor.execute("SELECT count(*) as count " + sql)
            count = cursor.fetchone()[0]
            queryset.count = lambda: count
            return queryset
        except:
            return Respondent.objects.none()



class PollResponse(models.Model):
    """
    Represents a response to a Poll.
    """
    poll = models.ForeignKey(Poll, related_name="responses")
    respondent = models.ForeignKey(Respondent, related_name="responses")
    
    message = models.ForeignKey(Message, null=True, blank=True)
    text = models.CharField(max_length=160)
    category = models.ForeignKey(PollCategory, null=True, related_name="primary_responses")
    secondary_category = models.ForeignKey(PollCategory, null=True, related_name="secondary_responses")
    active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)

    objects = ActiveManager()
    all = models.Manager()

    #def delete(self, using=None):
    #    print "deleting response %s" % self
    #    super(PollResponse, self).delete(using=using)

    def get_absolute_url(self):
        """
        Categories are viewed in the context of their poll
        """
        return reverse('poll_view', args=[self.poll.id])

    def __unicode__(self):
        return self.text

    class Meta:
        ordering = ('-id',)

class DemographicQuestion(SmartModel):
    """
    An arbitrary demographic question which can be answered in plain text
    """
    question = models.CharField(max_length=255, help_text="The text of the question, shown to the call center representative")
    priority = models.IntegerField(default=0, blank=True, null=True, help_text="The priority for this question, higher priority questions are show first")


class DemographicQuestionResponse(models.Model):
    question = models.ForeignKey(DemographicQuestion, related_name="answers")
    respondent = models.ForeignKey(Respondent, related_name="question_answers")
    response = models.TextField(max_length=255, help_text="The actual text of the response")

def edit_distance(s1, s2):
    """
    Compute the Damerau-Levenshtein distance between two given
    strings (s1 and s2)
    """
    d = {}
    lenstr1 = len(s1)
    lenstr2 = len(s2)
    for i in xrange(-1,lenstr1+1):
        d[(i,-1)] = i+1
    for j in xrange(-1,lenstr2+1):
        d[(-1,j)] = j+1
 
    for i in xrange(0,lenstr1):
        for j in xrange(0,lenstr2):
            if s1[i] == s2[j]:
                cost = 0
            else:
                cost = 1
            d[(i,j)] = min(
                           d[(i-1,j)] + 1, # deletion
                           d[(i,j-1)] + 1, # insertion
                           d[(i-1,j-1)] + cost, # substitution
                          )
            if i>1 and j>1 and s1[i]==s2[j-1] and s1[i-1] == s2[j]:
                d[(i,j)] = min (d[(i,j)], d[i-2,j-2] + cost) # transposition
 
    return d[lenstr1-1,lenstr2-1]

def trim_keyword(message, keyword=None):
    """
    Given a string, finds a keyword, then the rest of the message.  If there isn't at
    least one word in the message, returns none.
    """
    regex = "^[\s\d\.]*([a-z0-9]+)[^0-9a-z]?(.*)"
    if keyword:
        regex = "^[\s\d\.]*(" + keyword + ")[^0-9a-z]?(.*)"
    
    # do we match?
    match = re.match(regex, message, re.IGNORECASE)

    # if so, return the rest of the message
    if match:
        return (match.group(1), match.group(2))

    # otherwise, return none
    return None



