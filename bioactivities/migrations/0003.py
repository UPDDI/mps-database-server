# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bioactivities', '0002'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bioactivity',
            name='chembl_assay_type',
        ),
        migrations.RemoveField(
            model_name='pubchemassay',
            name='organism',
        ),
        migrations.RemoveField(
            model_name='pubchemassay',
            name='target_type',
        ),
        migrations.AddField(
            model_name='assay',
            name='name',
            field=models.TextField(default=b'', verbose_name=b'Assay Name'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assay',
            name='pubchem_id',
            field=models.TextField(default=b'', verbose_name=b'PubChem ID'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assay',
            name='source',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assay',
            name='source_id',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='assay',
            name='target',
            field=models.ForeignKey(default=None, blank=True, to='bioactivities.Target', null=True, verbose_name=b'Target', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pubchembioactivity',
            name='normalized_value',
            field=models.FloatField(null=True, verbose_name=b'Value (uM)', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pubchembioactivity',
            name='outcome',
            field=models.TextField(default=b'', verbose_name=b'Bioactivity Outcome'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='pubchemtarget',
            name='target_type',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='target',
            name='GI',
            field=models.TextField(default=b'', verbose_name=b'NCBI GI'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='assay_type',
            field=models.CharField(default=b'U', max_length=1, choices=[(b'B', b'Binding'), (b'F', b'Functional'), (b'A', b'ADMET'), (b'P', b'Physicochemical'), (b'U', b'Unknown')]),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='chemblid',
            field=models.TextField(default=b'', help_text=b'Enter a ChEMBL id, e.g. CHEMBL1217643, and click Retrieve to get target information automatically.', verbose_name=b'ChEMBL ID'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='description',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='journal',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='organism',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='assay',
            name='strain',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='description',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='name',
            field=models.TextField(default=b'', verbose_name=b'Assay Name'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='source',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='source_id',
            field=models.TextField(default=b''),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='assay',
            field=models.ForeignKey(blank=True, to='bioactivities.Assay', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='target',
            field=models.ForeignKey(default=None, blank=True, to='bioactivities.Target', null=True, verbose_name=b'Target', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='pubchemtarget',
            name='GI',
            field=models.TextField(null=True, verbose_name=b'NCBI GI', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='target',
            name='chemblid',
            field=models.TextField(help_text=b'Enter a ChEMBL id, e.g. CHEMBL260, and click Retrieve to get target information automatically.', null=True, verbose_name=b'ChEMBL ID', blank=True),
            preserve_default=True,
        ),
    ]
