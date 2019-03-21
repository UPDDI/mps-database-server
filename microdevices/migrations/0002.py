# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='organmodel',
            options={'ordering': ('model_name', 'organ'), 'verbose_name': 'Organ Model'},
        ),
        migrations.AddField(
            model_name='microdevice',
            name='column_labels',
            field=models.CharField(help_text=b'Space separated list of unique labels, e.g. "1 2 3 4 ...". Number of items must match number of columns.', max_length=1000, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='device_type',
            field=models.CharField(default=1, max_length=8, choices=[(b'chip', b'Microchip'), (b'plate', b'Plate')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='number_of_columns',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='number_of_rows',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='row_labels',
            field=models.CharField(help_text=b'Space separated list of unique labels, e.g. "A B C D ..." Number of items must match number of columns.', max_length=1000, null=True, blank=True),
            preserve_default=True,
        ),
    ]
