# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'CellSubtype.created_by'
        db.add_column(u'cellsamples_cellsubtype', 'created_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='cellsubtype_created-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellSubtype.created_on'
        db.add_column(u'cellsamples_cellsubtype', 'created_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellSubtype.modified_by'
        db.add_column(u'cellsamples_cellsubtype', 'modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='cellsubtype_modified-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellSubtype.modified_on'
        db.add_column(u'cellsamples_cellsubtype', 'modified_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellSubtype.signed_off_by'
        db.add_column(u'cellsamples_cellsubtype', 'signed_off_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='cellsubtype_signed_off_by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellSubtype.signed_off_date'
        db.add_column(u'cellsamples_cellsubtype', 'signed_off_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellSubtype.locked'
        db.add_column(u'cellsamples_cellsubtype', 'locked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Supplier.created_by'
        db.add_column(u'cellsamples_supplier', 'created_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='supplier_created-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Supplier.created_on'
        db.add_column(u'cellsamples_supplier', 'created_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Supplier.modified_by'
        db.add_column(u'cellsamples_supplier', 'modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='supplier_modified-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Supplier.modified_on'
        db.add_column(u'cellsamples_supplier', 'modified_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Supplier.signed_off_by'
        db.add_column(u'cellsamples_supplier', 'signed_off_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='supplier_signed_off_by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Supplier.signed_off_date'
        db.add_column(u'cellsamples_supplier', 'signed_off_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Supplier.locked'
        db.add_column(u'cellsamples_supplier', 'locked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Organ.created_by'
        db.add_column(u'cellsamples_organ', 'created_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='organ_created-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Organ.created_on'
        db.add_column(u'cellsamples_organ', 'created_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Organ.modified_by'
        db.add_column(u'cellsamples_organ', 'modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='organ_modified-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Organ.modified_on'
        db.add_column(u'cellsamples_organ', 'modified_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Organ.signed_off_by'
        db.add_column(u'cellsamples_organ', 'signed_off_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='organ_signed_off_by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'Organ.signed_off_date'
        db.add_column(u'cellsamples_organ', 'signed_off_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'Organ.locked'
        db.add_column(u'cellsamples_organ', 'locked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'CellType.created_by'
        db.add_column(u'cellsamples_celltype', 'created_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='celltype_created-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellType.created_on'
        db.add_column(u'cellsamples_celltype', 'created_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellType.modified_by'
        db.add_column(u'cellsamples_celltype', 'modified_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='celltype_modified-by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellType.modified_on'
        db.add_column(u'cellsamples_celltype', 'modified_on',
                      self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellType.signed_off_by'
        db.add_column(u'cellsamples_celltype', 'signed_off_by',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='celltype_signed_off_by', null=True, to=orm['auth.User']),
                      keep_default=False)

        # Adding field 'CellType.signed_off_date'
        db.add_column(u'cellsamples_celltype', 'signed_off_date',
                      self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'CellType.locked'
        db.add_column(u'cellsamples_celltype', 'locked',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'CellSubtype.created_by'
        db.delete_column(u'cellsamples_cellsubtype', 'created_by_id')

        # Deleting field 'CellSubtype.created_on'
        db.delete_column(u'cellsamples_cellsubtype', 'created_on')

        # Deleting field 'CellSubtype.modified_by'
        db.delete_column(u'cellsamples_cellsubtype', 'modified_by_id')

        # Deleting field 'CellSubtype.modified_on'
        db.delete_column(u'cellsamples_cellsubtype', 'modified_on')

        # Deleting field 'CellSubtype.signed_off_by'
        db.delete_column(u'cellsamples_cellsubtype', 'signed_off_by_id')

        # Deleting field 'CellSubtype.signed_off_date'
        db.delete_column(u'cellsamples_cellsubtype', 'signed_off_date')

        # Deleting field 'CellSubtype.locked'
        db.delete_column(u'cellsamples_cellsubtype', 'locked')

        # Deleting field 'Supplier.created_by'
        db.delete_column(u'cellsamples_supplier', 'created_by_id')

        # Deleting field 'Supplier.created_on'
        db.delete_column(u'cellsamples_supplier', 'created_on')

        # Deleting field 'Supplier.modified_by'
        db.delete_column(u'cellsamples_supplier', 'modified_by_id')

        # Deleting field 'Supplier.modified_on'
        db.delete_column(u'cellsamples_supplier', 'modified_on')

        # Deleting field 'Supplier.signed_off_by'
        db.delete_column(u'cellsamples_supplier', 'signed_off_by_id')

        # Deleting field 'Supplier.signed_off_date'
        db.delete_column(u'cellsamples_supplier', 'signed_off_date')

        # Deleting field 'Supplier.locked'
        db.delete_column(u'cellsamples_supplier', 'locked')

        # Deleting field 'Organ.created_by'
        db.delete_column(u'cellsamples_organ', 'created_by_id')

        # Deleting field 'Organ.created_on'
        db.delete_column(u'cellsamples_organ', 'created_on')

        # Deleting field 'Organ.modified_by'
        db.delete_column(u'cellsamples_organ', 'modified_by_id')

        # Deleting field 'Organ.modified_on'
        db.delete_column(u'cellsamples_organ', 'modified_on')

        # Deleting field 'Organ.signed_off_by'
        db.delete_column(u'cellsamples_organ', 'signed_off_by_id')

        # Deleting field 'Organ.signed_off_date'
        db.delete_column(u'cellsamples_organ', 'signed_off_date')

        # Deleting field 'Organ.locked'
        db.delete_column(u'cellsamples_organ', 'locked')

        # Deleting field 'CellType.created_by'
        db.delete_column(u'cellsamples_celltype', 'created_by_id')

        # Deleting field 'CellType.created_on'
        db.delete_column(u'cellsamples_celltype', 'created_on')

        # Deleting field 'CellType.modified_by'
        db.delete_column(u'cellsamples_celltype', 'modified_by_id')

        # Deleting field 'CellType.modified_on'
        db.delete_column(u'cellsamples_celltype', 'modified_on')

        # Deleting field 'CellType.signed_off_by'
        db.delete_column(u'cellsamples_celltype', 'signed_off_by_id')

        # Deleting field 'CellType.signed_off_date'
        db.delete_column(u'cellsamples_celltype', 'signed_off_date')

        # Deleting field 'CellType.locked'
        db.delete_column(u'cellsamples_celltype', 'locked')


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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'cellsamples.cellsample': {
            'Meta': {'ordering': "('cell_type', 'cell_source', 'id')", 'object_name': 'CellSample'},
            'barcode': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'cell_image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'cell_source': ('django.db.models.fields.CharField', [], {'default': "'Primary'", 'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'cell_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cellsamples.CellType']"}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsample_created-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isolation_datetime': ('django.db.models.fields.DateTimeField', [], {}),
            'isolation_method': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'isolation_notes': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsample_modified-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'patient_age': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'patient_condition': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'patient_gender': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1', 'blank': 'True'}),
            'percent_viability': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'product_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'receipt_date': ('django.db.models.fields.DateField', [], {}),
            'signed_off_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsample_signed_off_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'signed_off_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'supplier': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cellsamples.Supplier']"}),
            'viable_count': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'viable_count_unit': ('django.db.models.fields.CharField', [], {'default': "'N'", 'max_length': '1', 'blank': 'True'})
        },
        u'cellsamples.cellsubtype': {
            'Meta': {'ordering': "('cell_subtype',)", 'object_name': 'CellSubtype'},
            'cell_subtype': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsubtype_created-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsubtype_modified-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'signed_off_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'cellsubtype_signed_off_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'signed_off_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'cellsamples.celltype': {
            'Meta': {'ordering': "('species', 'cell_type', 'cell_subtype')", 'unique_together': "[('cell_type', 'species', 'cell_subtype')]", 'object_name': 'CellType'},
            'cell_subtype': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cellsamples.CellSubtype']"}),
            'cell_type': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'celltype_created-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'celltype_modified-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'organ': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['cellsamples.Organ']"}),
            'signed_off_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'celltype_signed_off_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'signed_off_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'species': ('django.db.models.fields.CharField', [], {'default': "'Human'", 'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        u'cellsamples.organ': {
            'Meta': {'ordering': "('organ_name',)", 'object_name': 'Organ'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'organ_created-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'organ_modified-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'organ_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'signed_off_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'organ_signed_off_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'signed_off_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'cellsamples.supplier': {
            'Meta': {'ordering': "('name',)", 'object_name': 'Supplier'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'supplier_created-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'created_on': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'locked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'supplier_modified-by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'modified_on': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'signed_off_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'supplier_signed_off_by'", 'null': 'True', 'to': u"orm['auth.User']"}),
            'signed_off_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['cellsamples']