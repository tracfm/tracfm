# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Point'
        db.create_table('simple_locations_point', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(max_digits=13, decimal_places=10)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(max_digits=13, decimal_places=10)),
        ))
        db.send_create_signal('simple_locations', ['Point'])

        # Adding model 'AreaType'
        db.create_table('simple_locations_areatype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=30, db_index=True)),
        ))
        db.send_create_signal('simple_locations', ['AreaType'])

        # Adding model 'Area'
        db.create_table('simple_locations_area', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('code_generator.fields.CodeField')(unique=True, max_length=50, blank=True)),
            ('kind', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simple_locations.AreaType'], null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['simple_locations.Point'], null=True, blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='children', null=True, to=orm['simple_locations.Area'])),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('simple_locations', ['Area'])

        # Adding unique constraint on 'Area', fields ['code', 'kind']
        db.create_unique('simple_locations_area', ['code', 'kind_id'])

        # Adding unique constraint on 'Area', fields ['name', 'kind']
        db.create_unique('simple_locations_area', ['name', 'kind_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Area', fields ['name', 'kind']
        db.delete_unique('simple_locations_area', ['name', 'kind_id'])

        # Removing unique constraint on 'Area', fields ['code', 'kind']
        db.delete_unique('simple_locations_area', ['code', 'kind_id'])

        # Deleting model 'Point'
        db.delete_table('simple_locations_point')

        # Deleting model 'AreaType'
        db.delete_table('simple_locations_areatype')

        # Deleting model 'Area'
        db.delete_table('simple_locations_area')


    models = {
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

    complete_apps = ['simple_locations']
