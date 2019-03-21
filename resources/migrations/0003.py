# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resource',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='resourcesubtype',
            name='description',
            field=models.TextField(default=b'', max_length=400, blank=True),
        ),
        migrations.AlterField(
            model_name='resourcetype',
            name='description',
            field=models.CharField(default=b'', max_length=400, blank=True),
        ),
    ]
