# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bioactivities', '0004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pubchemtarget',
            name='GI',
            field=models.TextField(default=b'', verbose_name=b'NCBI GI', blank=True),
        ),
    ]
