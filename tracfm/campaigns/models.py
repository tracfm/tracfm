from django.db import models
from smartmin.models import SmartModel
from polls.models import Poll

class Campaign(SmartModel):
    name = models.CharField(max_length=128, help_text="The name of this campaign")
    description = models.TextField(help_text="A short description, including the goals of the campaign.")
    story = models.TextField(help_text="The body of the campaign story")
    video_link = models.CharField(max_length=256, blank=True, null=True, help_text="A link to a video hosted on youtube.")
    polls = models.ManyToManyField(Poll, help_text="The polls that are part of this campaign", related_name="campaigns")
    priority = models.IntegerField(default=0, blank=True, null=True)
    background = models.CharField(default="#333333", max_length="12", 
                                  help_text="The color to use for the background of the story, ex: #2d66ae")

    @classmethod
    def set_poll_campaign(cls, poll, new_campaign):
        # first clear other campaigns this poll is part of
        for campaign in Campaign.objects.filter(polls=poll):
            campaign.polls.remove(poll)

        # then set this campaign just for this poll
        if new_campaign:
            new_campaign.polls.add(poll)

    def sorted_images(self):
        return self.images.order_by('-priority')

    def feature_image(self):
        images = self.sorted_images()
        if images:
            return images[0]

    def __unicode__(self):
        return self.name

class CampaignImage(models.Model):
    campaign = models.ForeignKey(Campaign, related_name='images')
    image = models.ImageField(upload_to='campaign_images/', width_field="width", height_field="height")
    caption = models.CharField(max_length=64)
    priority = models.IntegerField(default=0, blank=True, null=True)
    width = models.IntegerField()
    height = models.IntegerField()

    def __unicode__(self):
        return self.image.url
