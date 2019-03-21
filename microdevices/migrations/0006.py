# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='manufacturer',
            name='contact_person',
            field=models.CharField(default=b'', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='barcode',
            field=models.CharField(default=b'', max_length=200, verbose_name=b'version/ catalog#', blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='column_labels',
            field=models.CharField(default=b'', help_text=b'Space separated list of unique labels, e.g. "1 2 3 4 ...". Number of items must match number of columns.', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='device_size_unit',
            field=models.CharField(default=b'', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='row_labels',
            field=models.CharField(default=b'', help_text=b'Space separated list of unique labels, e.g. "A B C D ..." Number of items must match number of columns.', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='microdevice',
            name='substrate_material',
            field=models.CharField(default=b'', max_length=150, blank=True),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='contact_person',
            field=models.CharField(default=b'', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='organmodel',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
    ]
