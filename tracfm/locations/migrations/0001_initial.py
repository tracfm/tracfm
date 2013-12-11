# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Area'
        db.create_table('locations_area', (
            ('area_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['simple_locations.Area'], unique=True, primary_key=True)),
        ))
        db.send_create_signal('locations', ['Area'])

        # Adding model 'AreaRule'
        db.create_table('locations_arearule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='rules', to=orm['locations.Area'])),
            ('match', self.gf('django.db.models.fields.CharField')(max_length=65)),
            ('order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('locations', ['AreaRule'])


    def backwards(self, orm):
        
        # Deleting model 'Area'
        db.delete_table('locations_area')

        # Deleting model 'AreaRule'
        db.delete_table('locations_arearule')


    models = {
        'locations.area': {
            'Meta': {'object_name': 'Area', '_ormbases': ['simple_locations.Area']},
            'area_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['simple_locations.Area']", 'unique': 'True', 'primary_key': 'True'})
        },
        'locations.arearule': {
            'Meta': {'object_name': 'AreaRule'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rules'", 'to': "orm['locations.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.CharField', [], {'max_length': '65'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'simple_locations.area': {
            'Meta': {'unique_together': "(('code', 'kind'), ('name', 'kind'))", 'object_name': 'Area'},
            'code': ('code_generator.fields.CodeField', [], {'unique': 'True', 'max_length': '50', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['simple_locations.AreaType']", 'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'location': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['simple_locations.Point']", 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['simple_locations.Area']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'simple_locations.areatype': {
            'Meta': {'object_name': 'AreaType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '30', 'db_index': 'True'})
        },
        'simple_locations.point': {
            'Meta': {'object_name': 'Point'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '13', 'decimal_places': '10'})
        }
    }

    complete_apps = ['locations']
