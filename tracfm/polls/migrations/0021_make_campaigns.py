# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        from campaigns.models import Campaign
        from django_quickblocks.models import QuickBlock, QuickBlockType, QuickBlockImage
        from django.contrib.auth.models import User

        # create a quickblocktype for campaigns
        campaign_type = QuickBlockType.objects.filter(slug='campaign')
        if not campaign_type:
            campaign_type = QuickBlockType.objects.create(name="Campaign",
                                                          slug='campaign',
                                                          has_color=True,
                                                          has_image=True,
                                                          has_rich_text=True,
                                                          has_gallery=True,
                                                          has_video=True,
                                                          has_summary=True,
                                                          has_link=False,
                                                          created_by=User.objects.get(pk=1),
                                                          modified_by=User.objects.get(pk=1))
        else:
            campaign_type = campaign_type[0]

        # for each campaign
        for campaign in Campaign.objects.filter(is_active=True):
            quickblock = QuickBlock.objects.create(quickblock_type=campaign_type,
                                                   title=campaign.name,
                                                   summary=campaign.description,
                                                   content=campaign.story,
                                                   video_id=campaign.video_link,
                                                   priority=campaign.priority,
                                                   color=campaign.background,
                                                   created_by=campaign.created_by,
                                                   modified_by=campaign.modified_by)

            # set this quickblock on all the polls
            for poll in campaign.polls.all():
                poll.campaign = quickblock
                poll.save()

            # get our images
            images = campaign.sorted_images()

            from os import path
            from django.core.files.base import File

            # if we have some images, the first is our main image
            if images:
                try:
                    im = images[0]
                    f = open(im.image.path)
                    quickblock.image.save(path.basename(im.image.path), File(f), True)
                    f.close()
                except:
                    pass

            for (index, im) in enumerate(images[1:]):
                try:
                    f = open(im.image.path)
                    qbi = QuickBlockImage.objects.create(quickblock=quickblock,
                                                         priority=im.priority,
                                                         caption=im.caption,
                                                         image=File(f),
                                                         created_by=quickblock.created_by,
                                                         modified_by=quickblock.modified_by)
                    f.close()
                except:
                    pass

    def backwards(self, orm):
        from campaigns.models import Campaign
        from django_quickblocks.models import QuickBlock, QuickBlockType, QuickBlockImage

        QuickBlockImage.objects.filter(quickblock__quickblock_type__slug='campaign').delete()
        QuickBlock.objects.filter(quickblock_type__slug='campaign').delete()
        QuickBlockType.objects.filter(slug='campaign').delete()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'django_quickblocks.quickblock': {
            'Meta': {'object_name': 'QuickBlock'},
            'color': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quickblock_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'link': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quickblock_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'quickblock_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django_quickblocks.QuickBlockType']"}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'video_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        },
        'django_quickblocks.quickblocktype': {
            'Meta': {'object_name': 'QuickBlockType'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quickblocktype_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'has_color': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_gallery': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_image': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_link': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_rich_text': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_summary': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_tags': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'has_title': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'has_video': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'quickblocktype_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '75'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'polls.demographicquestion': {
            'Meta': {'object_name': 'DemographicQuestion'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'demographicquestion_creations'", 'to': "orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'demographicquestion_modifications'", 'to': "orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'question': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'polls.demographicquestionresponse': {
            'Meta': {'object_name': 'DemographicQuestionResponse'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['polls.DemographicQuestion']"}),
            'respondent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'question_answers'", 'to': "orm['polls.Respondent']"}),
            'response': ('django.db.models.fields.TextField', [], {'max_length': '255'})
        },
        'polls.poll': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Poll'},
            'always_update': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'audio_file': ('django.db.models.fields.CharField', [], {'max_length': '512', 'null': 'True', 'blank': 'True'}),
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']", 'null': 'True'}),
            'campaign': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['django_quickblocks.QuickBlock']", 'null': 'True'}),
            'category_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'category_set'", 'null': 'True', 'to': "orm['polls.PollCategorySet']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'demographic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'detailed_chart': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'secondary_category_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'secondary_category_set'", 'null': 'True', 'to': "orm['polls.PollCategorySet']"}),
            'secondary_template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'secondary_template'", 'null': 'True', 'to': "orm['polls.PollCategorySet']"}),
            'started': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'template': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'template'", 'null': 'True', 'to': "orm['polls.PollCategorySet']"}),
            'unknown_message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'polls.pollcategory': {
            'Meta': {'unique_together': "(('name', 'category_set'),)", 'object_name': 'PollCategory'},
            'category_set': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'categories'", 'to': "orm['polls.PollCategorySet']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'longitude': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'})
        },
        'polls.pollcategoryset': {
            'Meta': {'object_name': 'PollCategorySet'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polls.Poll']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'polls.pollkeyword': {
            'Meta': {'object_name': 'PollKeyword'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'keywords'", 'to': "orm['polls.Poll']"})
        },
        'polls.pollresponse': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'PollResponse'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_responses'", 'null': 'True', 'to': "orm['polls.PollCategory']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms_httprouter.Message']", 'null': 'True', 'blank': 'True'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': "orm['polls.Poll']"}),
            'respondent': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'responses'", 'to': "orm['polls.Respondent']"}),
            'secondary_category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'secondary_responses'", 'null': 'True', 'to': "orm['polls.PollCategory']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '160'})
        },
        'polls.pollrule': {
            'Meta': {'ordering': "('order', '-category')", 'object_name': 'PollRule'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rules'", 'to': "orm['polls.PollCategory']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lower_bound': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'match': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'numeric': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'upper_bound': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        },
        'polls.respondent': {
            'Meta': {'object_name': 'Respondent'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'db_index': 'True'}),
            'last_response': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'last_respondent'", 'null': 'True', 'to': "orm['polls.PollResponse']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'notes': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'polls.tracsettings': {
            'Meta': {'object_name': 'TracSettings'},
            'duplicate_message': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recruitment_message': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'trac_off_response': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'trac_on_response': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'trac_reset_response': ('django.db.models.fields.CharField', [], {'max_length': '160'})
        },
        'rapidsms.backend': {
            'Meta': {'object_name': 'Backend'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20'})
        },
        'rapidsms.connection': {
            'Meta': {'object_name': 'Connection'},
            'backend': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Backend']"}),
            'contact': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Contact']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        'rapidsms_httprouter.message': {
            'Meta': {'object_name': 'Message'},
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'messages'", 'to': "orm['rapidsms.Connection']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'delivered': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_response_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responses'", 'null': 'True', 'to': "orm['rapidsms_httprouter.Message']"}),
            'sent': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'text': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['polls']
    symmetrical = True
