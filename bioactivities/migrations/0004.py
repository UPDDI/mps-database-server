# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bioactivities', '0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='bioactivity',
            name='data_validity',
            field=models.CharField(default=b'', max_length=1, blank=True, choices=[(b'R', b'Outside typical range'), (b'T', b'Potential transcription error'), (b'O', b'Other')]),
        ),
        migrations.AddField(
            model_name='bioactivity',
            name='normalized_value',
            field=models.FloatField(null=True, verbose_name=b'Normalized Value', blank=True),
        ),
        migrations.AddField(
            model_name='bioactivity',
            name='notes',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AddField(
            model_name='pubchembioactivity',
            name='data_validity',
            field=models.CharField(default=b'', max_length=1, blank=True, choices=[(b'R', b'Outside typical range'), (b'T', b'Potential transcription error'), (b'O', b'Other')]),
        ),
        migrations.AddField(
            model_name='pubchembioactivity',
            name='notes',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='chemblid',
            field=models.TextField(default=b'', help_text=b'Enter a ChEMBL id, e.g. CHEMBL1217643, and click Retrieve to get target information automatically.', verbose_name=b'ChEMBL ID', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='journal',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='name',
            field=models.TextField(default=b'', verbose_name=b'Assay Name', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='organism',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='pubchem_id',
            field=models.TextField(default=b'', verbose_name=b'PubChem ID', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='source',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='source_id',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='assay',
            name='strain',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='activity_comment',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='bioactivity_type',
            field=models.TextField(default=b'', verbose_name=b'name', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='name_in_reference',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='operator',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='reference',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='standard_name',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='standardized_units',
            field=models.TextField(default=b'', verbose_name=b'std units', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivity',
            name='units',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivitytype',
            name='chembl_bioactivity',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivitytype',
            name='chembl_unit',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivitytype',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivitytype',
            name='standard_name',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='bioactivitytype',
            name='standard_unit',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='name',
            field=models.TextField(default=b'', verbose_name=b'Assay Name', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='source',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemassay',
            name='source_id',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='activity_name',
            field=models.TextField(default=b'', verbose_name=b'Activity Name', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='normalized_value',
            field=models.FloatField(null=True, verbose_name=b'Normalized Value', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='outcome',
            field=models.TextField(default=b'', verbose_name=b'Bioactivity Outcome', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchembioactivity',
            name='target',
            field=models.ForeignKey(verbose_name=b'Target', blank=True, to='bioactivities.Target', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='pubchemtarget',
            name='name',
            field=models.TextField(default=b'', help_text=b'Preferred target name.', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemtarget',
            name='organism',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='pubchemtarget',
            name='target_type',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='GI',
            field=models.TextField(default=b'', verbose_name=b'NCBI GI', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='chemblid',
            field=models.TextField(default=b'', help_text=b'Enter a ChEMBL id, e.g. CHEMBL260, and click Retrieve to get target information automatically.', verbose_name=b'ChEMBL ID', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='description',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='gene_names',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='organism',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='synonyms',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='target_type',
            field=models.TextField(default=b'', blank=True),
        ),
        migrations.AlterField(
            model_name='target',
            name='uniprot_accession',
            field=models.TextField(default=b'', blank=True),
        ),
    ]
