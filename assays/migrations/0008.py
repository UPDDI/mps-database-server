# -*- coding: utf-8 -*-


from django.db import models, migrations
import assays.models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='assaylayout',
            name='standard',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayreadout',
            name='quality',
            field=models.CharField(default=b'', max_length=10),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='file',
            field=models.FileField(help_text=b'Green = Data from database; Red = Line that will not be read; Gray = Reading with null value ***Uploading overwrites old data***', upload_to=assays.models.chip_readout_file_location, null=True, verbose_name=b'Data File', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychiptestresult',
            name='summary',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='file',
            field=models.FileField(upload_to=assays.models.plate_readout_file_location, null=True, verbose_name=b'Data File', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayplatetestresult',
            name='summary',
            field=models.TextField(default=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='assayplatereadoutassay',
            unique_together=set([('readout_id', 'assay_id', 'feature')]),
        ),
    ]
