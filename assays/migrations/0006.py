# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='assaymodel',
            name='assay_short_name',
            field=models.CharField(max_length=10, unique=True, null=True),
            preserve_default=True,
        ),
    ]
