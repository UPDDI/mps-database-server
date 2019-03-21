# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cellsamples', '0002'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cellsample',
            name='viable_count_unit',
        ),
        migrations.AddField(
            model_name='cellsample',
            name='cell_subtype',
            field=models.ForeignKey(default=1, to='cellsamples.CellSubtype', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='flagged',
            field=models.BooleanField(default=False, help_text=b'Check box to flag for review'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='reason_for_flag',
            field=models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsubtype',
            name='cell_type',
            field=models.ForeignKey(blank=True, to='cellsamples.CellType', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='celltype',
            name='cell_subtype',
            field=models.ForeignKey(blank=True, to='cellsamples.CellSubtype', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='celltype',
            name='species',
            field=models.CharField(default=b'Human', max_length=10, null=True, blank=True, choices=[(b'Human', b'Human'), (b'Rat', b'Rat'), (b'Mouse', b'Mouse')]),
            preserve_default=True,
        ),
    ]
