# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):

        # we've got extra respondents per backend
        for respondent in orm.Respondent.objects.all().order_by('id'):

            # get the idnetity from the connection
            connection = respondent.connection
            respondent.identity = connection.identity
            respondent.save()

            # all remaining respondents with our identity will become us
            for other in orm.Respondent.objects.filter(connection__identity=connection.identity).exclude(id=respondent.id):

                # if any respondent is active mark the master active
                if other.active:
                    respondent.active = True
                    if other.active_date:
                        if not respondent.active_date or other.active_date > respondent.active_date:
                            respondent.active_date = other.active_date

                if other.last_response_id > respondent.last_response_id:
                    respondent.last_response_id = other.last_response_id

                respondent.save()

                # steal all of their poll responses
                for response in orm.PollResponse.objects.filter(respondent=other):
                    response.respondent = respondent
                    response.save()

                # buh-bye
                other.delete()

            # mark second responses to the same poll as inactive
            seen = dict()
            for response in respondent.responses.filter(active=True).order_by('created'):
                if response.poll.id not in seen:
                    seen[response.poll.id] = response
                else:
                    # already got a response for this poll, sorry pal
                    response.active = False
                    response.save()

    def backwards(self, orm):
        # Sorry, you lose.
        raise RuntimeError("Cannot reverse this migration.")


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
        'polls.poll': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'Poll'},
            'category_set': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'category_set'", 'null': 'True', 'to': "orm['polls.PollCategorySet']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'demographic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.SlugField', [], {'default': "''", 'max_length': '32', 'db_index': 'True', 'blank': 'True'}),
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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80'}),
            'poll': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['polls.Poll']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'polls.pollresponse': {
            'Meta': {'ordering': "('-id',)", 'object_name': 'PollResponse'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'primary_responses'", 'null': 'True', 'to': "orm['polls.PollCategory']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms_httprouter.Message']"}),
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
            'connection': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['rapidsms.Connection']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identity': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
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
            'trac_on_response': ('django.db.models.fields.CharField', [], {'max_length': '160'})
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
            'direction': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_response_to': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'responses'", 'null': 'True', 'to': "orm['rapidsms_httprouter.Message']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'text': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['polls']
