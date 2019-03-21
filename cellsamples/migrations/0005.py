# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cellsamples', '0004'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='celltype',
            options={'ordering': ('species', 'cell_type'), 'verbose_name': 'Cell Type'},
        ),
        migrations.RemoveField(
            model_name='cellsample',
            name='cell_source',
        ),
        migrations.AlterUniqueTogether(
            name='celltype',
            unique_together=set([('cell_type', 'species', 'organ')]),
        ),
        migrations.RemoveField(
            model_name='celltype',
            name='cell_subtype',
        ),
    ]
