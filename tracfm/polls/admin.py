from polls.models import Poll, PollCategory, PollCategorySet, PollRule, Respondent, PollResponse
from django.contrib import admin

admin.site.register(Poll)
admin.site.register(PollCategory)
admin.site.register(PollCategorySet)
admin.site.register(PollRule)
admin.site.register(PollResponse)
admin.site.register(Respondent)
