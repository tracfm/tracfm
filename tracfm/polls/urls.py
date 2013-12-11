from views import *
urlpatterns  = patterns('',
    url(r'^$', PollListView.as_view(), name="polls"),
    url(r'^start/(\d+)/$', poll_start, name="poll_start"),
    url(r'^stop/(\d+)/$', poll_stop, name="poll_stop"),                       
    url(r'^create/$', PollCreateView.as_view(), name="poll_create"),
    url(r'^edit/(?P<pk>\d+)/$', PollUpdateView.as_view(), name="poll_edit"),
    url(r'^view/(?P<pk>\d+)/$', PollDetailView.as_view(), name="poll_view"),
    url(r'^iframe/(?P<pk>\d+)/$', PollIFrameView.as_view(), name="poll_iframe"),
    url(r'^del/(?P<pk>\d+)/$', PollDeleteView.as_view(), name="poll_delete"),

    url(r'^demo/$', DemographicPollListView.as_view(), name="poll_demo_list"),
    url(r'^demo/create/$', DemographicPollCreateView.as_view(), name="poll_demo_create"),

    url(r'^responses/(?P<poll_id>\d+)/$', PollResponseListView.as_view(), name="responses_for_poll"),
    url(r'^responses/(?P<poll_id>\d+)/(?P<category_id>_)/$', PollResponseListView.as_view(), name="responses_for_poll"),
    url(r'^responses/(?P<poll_id>\d+)/(?P<category_id>\d+)/$', PollResponseListView.as_view(), name="responses_for_poll"),

    url(r'^responses/categorize/(?P<poll_id>\d+)/(?P<category_id>_)/$', ResponseCategorizationView.as_view(), name="response_categorization"),
    url(r'^responses/categorize/(?P<poll_id>\d+)/(?P<category_id>\d+)/$', ResponseCategorizationView.as_view(), name="response_categorization"),

    url(r'^catsets/$', PollCategorySetListView.as_view(), name="catsets_list"),
    url(r'^catsets/create/$', PollCategorySetCreateView.as_view(), name="catset_add"),
    url(r'^catsets/(?P<pk>\d+)/$', PollCategorySetDetailView.as_view(), name="catset_view"),
    url(r'^catsets/(?P<pk>\d+)/edit/$', PollCategorySetUpdateView.as_view(), name="catset_edit"),
    url(r'^catsets/(?P<pk>\d+)/del/$', PollCategorySetDeleteView.as_view(), name="catset_delete"),
    url(r'^catsets/(?P<catset_id>\d+)/create/$', PollCategoryCreateView.as_view(), name="category_create"),
    url(r'^catsets/(?P<catset_id>\d+)/(?P<pk>\d+)/$', PollCategoryUpdateView.as_view(), name="category_edit"),

    # for linking from poll page
    url(r'^category/(?P<pk>\d+)/$', PollCategorySetDetailView.as_view(), name="poll_catset_view"),
    url(r'^category/(?P<catset_id>\d+)/create/$', PollCategoryCreateView.as_view(), name="poll_category_create"),
    url(r'^category/(?P<catset_id>\d+)/(?P<pk>\d+)/$', PollCategoryUpdateView.as_view(), name="poll_category_edit"),
    url(r'^category/(?P<catset_id>\d+)/(?P<pk>\d+)/del$', PollCategoryDeleteView.as_view(), name="poll_category_delete"),
    url(r'^catsets/(?P<catset_id>\d+)/(?P<pk>\d+)/del$', PollCategoryDeleteView.as_view(), name="category_delete"),

    url(r'^respondents/$', RespondentListView.as_view(), name="respondents"),
    url(r'^respondents/view/(?P<pk>\d+)/$', RespondentDetailView.as_view(), name="respondent_view"),
    url(r'^respondents/edit/(?P<pk>\d+)/$', DemographicUpdateView.as_view(), name="respondent_edit"),
)

urlpatterns += DemographicQuestionCRUDL().as_urlpatterns()
urlpatterns += TracSettingsCRUDL().as_urlpatterns()
