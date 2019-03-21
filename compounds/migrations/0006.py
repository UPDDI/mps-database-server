# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='compoundtarget',
            name='action',
            field=models.CharField(default=b'', max_length=75, blank=True),
        ),
        migrations.AlterField(
            model_name='compoundtarget',
            name='uniprot_id',
            field=models.CharField(default=b'', max_length=20, blank=True),
        ),
    ]
