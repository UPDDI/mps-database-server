# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0004'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='readoutunit',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='readoutunit',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='readoutunit',
            name='signed_off_by',
        ),
        migrations.DeleteModel(
            name='ReadoutUnit',
        ),
        migrations.RemoveField(
            model_name='timeunits',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='timeunits',
            name='modified_by',
        ),
        migrations.RemoveField(
            model_name='timeunits',
            name='signed_off_by',
        ),
        migrations.DeleteModel(
            name='TimeUnits',
        ),
        migrations.AlterField(
            model_name='studymodel',
            name='label',
            field=models.CharField(max_length=2),
            preserve_default=True,
        ),
    ]
