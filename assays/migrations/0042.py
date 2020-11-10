# Generated by Django 2.2.15 on 2020-10-30 22:27

import assays.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assays', '0041'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayOmicAnalysisTarget',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Input File Headers for omics upload (e.g. baseMean, normscount). Do not change without checking with omic upload developer.', max_length=512, verbose_name='Input File Headers')),
                ('data_type', models.CharField(default='log2fc', help_text='Data Type (must match exactly the hardcoded assay omic data type choices). Do not change without checking with omic upload developer.', max_length=25, verbose_name='Data Type')),
                ('method', models.ForeignKey(help_text='Data Analysis Method (Computational Method). Do not change without checking with omic upload developer.', on_delete=django.db.models.deletion.CASCADE, to='assays.AssayMethod', verbose_name='Data Analysis Method')),
                ('target', models.ForeignKey(help_text='Data Analysis Target - computational feature.', on_delete=django.db.models.deletion.CASCADE, to='assays.AssayTarget', verbose_name='Data Analysis Target')),
                ('unit', models.ForeignKey(help_text='Data Analysis Unit - unit of computational feature.', on_delete=django.db.models.deletion.CASCADE, to='assays.PhysicalUnits', verbose_name='Data Analysis Unit')),
            ],
            options={
                'verbose_name': 'Assay Omic Analysis Target',
                'unique_together': {('name', 'data_type', 'method')},
            },
        ),
        migrations.CreateModel(
            name='AssayOmicDataFileUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(blank=True, null=True)),
                ('locked', models.BooleanField(default=False, help_text='Check the box and save to block automatic migration to *Public Access*, 1-year after sign off. Uncheck and save to enable automatic migration to *Public Access*, 1-year after sign off. While this is checked, automatic approvals for Stakeholders are also prevented.', verbose_name='Keep Private Indefinitely (Locked)')),
                ('description', models.CharField(default='file added - 20201030-18:27:26', help_text='Description of the data being uploaded in this file (e.g., "Treated vrs Control" or "Treated with 1uM Calcifidiol".', max_length=2000, verbose_name='Data Description')),
                ('omic_data_file', models.FileField(help_text='Omic data file to be uploaded to the database.', upload_to=assays.models.omic_data_file_location, verbose_name='Omic Data File*')),
                ('name_reference', models.CharField(choices=[('temposeq_probe', 'TempO-Seq Probe ID'), ('entrez_gene', 'NCBI Gene ID (Entrez)'), ('ensembl_gene', 'Ensemble Gene ID'), ('refseq_gene', 'RefSeq ID'), ('affymerix_probe', 'Affymerix Probeset ID'), ('gene_symbol', 'Gene Symbol')], default='temposeq_probe', help_text='Gene or probe ID (nomenclature used in import file)', max_length=25, verbose_name='Gene or Probe ID')),
                ('data_type', models.CharField(choices=[('log2fc', 'Log 2 Fold Change'), ('normcounts', 'Normalized Counts'), ('rawcounts', 'Raw Counts')], default='log2fc', help_text='Type of computational results.', max_length=25, verbose_name='Data Type')),
                ('time_1', models.FloatField(blank=True, default=0, help_text='Sample Time for the Test Group', null=True, verbose_name='Test Group Sample Time')),
                ('time_2', models.FloatField(blank=True, default=0, help_text='Sample Time for the Reference Group', null=True, verbose_name='Reference Group Sample Time')),
                ('analysis_method', models.ForeignKey(help_text='Data analysis method or computational tool (e.g. DESeq2).', on_delete=django.db.models.deletion.CASCADE, to='assays.AssayMethod', verbose_name='Data Analysis Method')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assayomicdatafileupload_created_by', to=settings.AUTH_USER_MODEL)),
                ('group_1', models.ForeignKey(blank=True, help_text='Data Processing Test Group', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_1', to='assays.AssayGroup', verbose_name='Test Group*')),
                ('group_2', models.ForeignKey(blank=True, help_text='Data Processing Reference Group', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='group_2', to='assays.AssayGroup', verbose_name='Reference Group*')),
                ('location_1', models.ForeignKey(blank=True, help_text='Sample Location for the Test Group', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='location_1', to='assays.AssaySampleLocation', verbose_name='Test Group Sample Location')),
                ('location_2', models.ForeignKey(blank=True, help_text='Sample Location for the Reference Group', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='location_2', to='assays.AssaySampleLocation', verbose_name='Reference Group Sample Location')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assayomicdatafileupload_modified_by', to=settings.AUTH_USER_MODEL)),
                ('signed_off_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assayomicdatafileupload_signed_off_by', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Assay Omic Data File Upload',
                'verbose_name_plural': 'Assay Omic Data File Uploads',
            },
        ),
        migrations.CreateModel(
            name='AbstractClassAssayStudyAssayOmic',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('assays.assaystudyassay',),
        ),
        migrations.AlterModelOptions(
            name='assaymatrixitem',
            options={'verbose_name': 'Study Item'},
        ),
        migrations.AddField(
            model_name='assaystudy',
            name='omics',
            field=models.BooleanField(default=False, verbose_name='Omics'),
        ),
        migrations.AlterField(
            model_name='assayplatereadermapdatafile',
            name='description',
            field=models.CharField(blank=True, default='file added - 20201030-18:27:26', max_length=2000, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='assaystudy',
            unique_together={('name', 'efficacy', 'disease', 'cell_characterization', 'omics', 'pbpk_steady_state', 'pbpk_bolus', 'start_date', 'group')},
        ),
        migrations.CreateModel(
            name='AssayOmicDataPoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Gene or Probe ID', max_length=100, verbose_name='Name')),
                ('value', models.FloatField(blank=True, null=True, verbose_name='Computed Value')),
                ('analysis_target', models.ForeignKey(help_text='Analysis Target', on_delete=django.db.models.deletion.CASCADE, to='assays.AssayOmicAnalysisTarget', verbose_name='Analysis Target')),
                ('omic_data_file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assays.AssayOmicDataFileUpload', verbose_name='Data File')),
                ('study', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assays.AssayStudy', verbose_name='This Study')),
            ],
            options={
                'verbose_name': 'Assay Omic Data Point',
                'verbose_name_plural': 'Assay Omic Data Points',
            },
        ),
        migrations.AddField(
            model_name='assayomicdatafileupload',
            name='study',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='assays.AssayStudy', verbose_name='This Study'),
        ),
        migrations.AddField(
            model_name='assayomicdatafileupload',
            name='study_assay',
            field=models.ForeignKey(help_text='Category, Target, Method, Unit as entered in the Study Assay Setup.', on_delete=django.db.models.deletion.CASCADE, to='assays.AssayStudyAssay', verbose_name='Upload File Assay'),
        ),
        migrations.AlterUniqueTogether(
            name='assayomicdatafileupload',
            unique_together={('study', 'omic_data_file')},
        ),
    ]
