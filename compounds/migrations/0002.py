# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='compound',
            name='tags',
            field=models.TextField(help_text=b'Tags for the compound (EPA, NCATS, etc.)', null=True, blank=True),
            preserve_default=True,
        ),
    ]
