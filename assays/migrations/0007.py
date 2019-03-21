# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='assaychiprawdata',
            name='quality',
            field=models.CharField(default=b'', max_length=20),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assaychiptestresult',
            name='summary',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayplatetestresult',
            name='summary',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assayrun',
            name='image',
            field=models.ImageField(null=True, upload_to=b'studies', blank=True),
            preserve_default=True,
        ),
    ]
