# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0019'),
    ]

    operations = [
        migrations.AddField(
            model_name='assayrun',
            name='flagged',
            field=models.BooleanField(default=False, help_text=b'Check box to flag for review'),
        ),
        migrations.AddField(
            model_name='assayrun',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
    ]
