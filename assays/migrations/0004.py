# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='physicalunits',
            name='availability',
            field=models.CharField(help_text='Type a series of strings for indicating where this unit should be listed:\ntest = test results\nreadouts = readouts', max_length=256, null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='physicalunits',
            name='base_unit',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='physicalunits',
            name='scale_factor',
            field=models.FloatField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychipcells',
            name='cell_biosensor',
            field=models.ForeignKey(default=2, to='cellsamples.Biosensor', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assaychipcells',
            name='cell_passage',
            field=models.CharField(max_length=16, null=True, verbose_name=b'Passage#', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assaychipreadoutassay',
            name='readout_unit',
            field=models.ForeignKey(to='assays.PhysicalUnits', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayplatecells',
            name='cell_biosensor',
            field=models.ForeignKey(default=2, to='cellsamples.Biosensor', on_delete=models.CASCADE),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='assayplatecells',
            name='cell_passage',
            field=models.CharField(max_length=16, null=True, verbose_name=b'Passage#', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assayplatereadoutassay',
            name='readout_unit',
            field=models.ForeignKey(to='assays.PhysicalUnits', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
