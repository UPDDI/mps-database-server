# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cellsamples', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cellsample',
            options={'ordering': ('-receipt_date',), 'verbose_name': 'Cell Sample'},
        ),
        migrations.AlterModelOptions(
            name='celltype',
            options={'ordering': ('species', 'cell_type', 'cell_subtype'), 'verbose_name': 'Cell Type'},
        ),
    ]
