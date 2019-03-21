# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('assays', '0024'),
    ]

    operations = [
        migrations.AddField(
            model_name='assayrun',
            name='access_groups',
            field=models.ManyToManyField(related_name='access_groups', to='auth.Group', blank=True),
        ),
    ]
