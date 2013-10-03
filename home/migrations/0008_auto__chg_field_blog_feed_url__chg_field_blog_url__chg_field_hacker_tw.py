# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Blog.feed_url'
        db.alter_column(u'home_blog', 'feed_url', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Blog.url'
        db.alter_column(u'home_blog', 'url', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Hacker.twitter'
        db.alter_column(u'home_hacker', 'twitter', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Hacker.github'
        db.alter_column(u'home_hacker', 'github', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Hacker.avatar_url'
        db.alter_column(u'home_hacker', 'avatar_url', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Post.title'
        db.alter_column(u'home_post', 'title', self.gf('django.db.models.fields.TextField')())

        # Changing field 'Post.url'
        db.alter_column(u'home_post', 'url', self.gf('django.db.models.fields.TextField')())

    def backwards(self, orm):

        # Changing field 'Blog.feed_url'
        db.alter_column(u'home_blog', 'feed_url', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Changing field 'Blog.url'
        db.alter_column(u'home_blog', 'url', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Changing field 'Hacker.twitter'
        db.alter_column(u'home_hacker', 'twitter', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Changing field 'Hacker.github'
        db.alter_column(u'home_hacker', 'github', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Changing field 'Hacker.avatar_url'
        db.alter_column(u'home_hacker', 'avatar_url', self.gf('django.db.models.fields.CharField')(max_length=400))

        # Changing field 'Post.title'
        db.alter_column(u'home_post', 'title', self.gf('django.db.models.fields.CharField')(max_length=200))

        # Changing field 'Post.url'
        db.alter_column(u'home_post', 'url', self.gf('django.db.models.fields.CharField')(max_length=400))

    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'home.blog': {
            'Meta': {'object_name': 'Blog'},
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'feed_url': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_crawled': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'home.comment': {
            'Meta': {'object_name': 'Comment'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'date_modified': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['home.Comment']", 'null': 'True', 'blank': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['home.Post']"}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "'xJnaPS'", 'unique': 'True', 'max_length': '6'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'home.hacker': {
            'Meta': {'object_name': 'Hacker'},
            'avatar_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'github': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'twitter': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['auth.User']", 'unique': 'True'})
        },
        u'home.post': {
            'Meta': {'object_name': 'Post'},
            'blog': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['home.Blog']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'default': "'i8Suqv'", 'unique': 'True', 'max_length': '6'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['home']