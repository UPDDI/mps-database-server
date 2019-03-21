# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayBaseLayout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('base_layout_name', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ('base_layout_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipCells',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cellsample_density', models.FloatField(default=0, verbose_name=b'density')),
                ('cellsample_density_unit', models.CharField(default=b'CP', max_length=8, verbose_name=b'Unit', choices=[(b'WE', b'cells / well'), (b'CP', b'cells / chip'), (b'ML', b'cells / mL'), (b'MM', b'cells / mm^2')])),
                ('cell_passage', models.CharField(default=b'-', max_length=16, verbose_name=b'Passage#')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipRawData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_id', models.CharField(default=b'0', max_length=255)),
                ('value', models.FloatField(null=True)),
                ('elapsed_time', models.FloatField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipReadout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
                ('treatment_time_length', models.FloatField(null=True, verbose_name=b'Assay Treatment Duration', blank=True)),
                ('readout_start_time', models.DateField(help_text=b'YYYY-MM-DD', verbose_name=b'Readout Start Date')),
                ('notebook', models.CharField(max_length=256, null=True, blank=True)),
                ('notebook_page', models.IntegerField(null=True, blank=True)),
                ('notes', models.CharField(max_length=2048, null=True, blank=True)),
                ('scientist', models.CharField(max_length=100, null=True, blank=True)),
                ('file', models.FileField(help_text=b'Green = Data from database; Red = Line that will not be read; Gray = Reading with null value ***Uploading overwrites old data***', upload_to=b'csv', null=True, verbose_name=b'Data File', blank=True)),
            ],
            options={
                'ordering': ('chip_setup',),
                'verbose_name': 'Chip Readout',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipReadoutAssay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_type', models.CharField(default=b'F', max_length=6, verbose_name=b'Object of Interest', choices=[(b'F', b'Field'), (b'C', b'Colony'), (b'O', b'Outflow'), (b'X', b'Other')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayChipSetup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
                ('setup_date', models.DateField(help_text=b'YYYY-MM-DD')),
                ('variance', models.CharField(max_length=3000, null=True, verbose_name=b'Variance from Protocol', blank=True)),
                ('assay_chip_id', models.CharField(max_length=512, verbose_name=b'Chip ID/ Barcode')),
                ('chip_test_type', models.CharField(max_length=8, choices=[(b'control', b'Control'), (b'compound', b'Compound')])),
                ('concentration', models.FloatField(default=0, null=True, verbose_name=b'Conc.', blank=True)),
                ('scientist', models.CharField(max_length=100, null=True, blank=True)),
                ('notebook', models.CharField(max_length=256, null=True, blank=True)),
                ('notebook_page', models.IntegerField(null=True, blank=True)),
                ('notes', models.CharField(max_length=2048, null=True, blank=True)),
            ],
            options={
                'ordering': ('-assay_chip_id', 'assay_run_id'),
                'verbose_name': 'Chip Setup',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayCompound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concentration', models.FloatField(default=0)),
                ('concentration_unit', models.CharField(default=b'\xce\xbcM', max_length=64)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayDeviceReadout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('assay_device_id', models.CharField(max_length=512, verbose_name=b'Plate ID/ Barcode')),
                ('cellsample_density', models.FloatField(default=0, verbose_name=b'density')),
                ('cellsample_density_unit', models.CharField(default=b'ML', max_length=8, verbose_name=b'Unit', choices=[(b'WE', b'cells / well'), (b'ML', b'cells / mL'), (b'MM', b'cells / mm^2')])),
                ('treatment_time_length', models.FloatField(null=True, verbose_name=b'Treatment Duration', blank=True)),
                ('assay_start_time', models.DateField(help_text=b'YYYY-MM-DD', null=True, verbose_name=b'Start Date', blank=True)),
                ('readout_start_time', models.DateField(help_text=b'YYYY-MM-DD', null=True, verbose_name=b'Readout Date', blank=True)),
                ('notebook', models.CharField(max_length=256, null=True, blank=True)),
                ('notebook_page', models.IntegerField(null=True, blank=True)),
                ('notes', models.CharField(max_length=2048, null=True, blank=True)),
                ('scientist', models.CharField(max_length=100, null=True, blank=True)),
                ('file', models.FileField(upload_to=b'csv', null=True, verbose_name=b'Data File', blank=True)),
            ],
            options={
                'ordering': ('assay_device_id', 'assay_name'),
                'verbose_name': 'Plate Readout',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayLayout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('layout_name', models.CharField(max_length=200)),
            ],
            options={
                'ordering': ('layout_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayLayoutFormat',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('layout_format_name', models.CharField(unique=True, max_length=200)),
                ('number_of_rows', models.IntegerField()),
                ('number_of_columns', models.IntegerField()),
                ('row_labels', models.CharField(help_text=b'Space separated list of unique labels, e.g. "A B C D ..." Number of items must match number of columns.', max_length=1000)),
                ('column_labels', models.CharField(help_text=b'Space separated list of unique labels, e.g. "1 2 3 4 ...". Number of items must match number of columns.', max_length=1000)),
            ],
            options={
                'ordering': ('layout_format_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('assay_name', models.CharField(unique=True, max_length=200)),
                ('version_number', models.CharField(max_length=200, null=True, verbose_name=b'Version', blank=True)),
                ('assay_description', models.TextField(null=True, verbose_name=b'Description', blank=True)),
                ('assay_protocol_file', models.FileField(upload_to=b'assays', null=True, verbose_name=b'Protocol File', blank=True)),
                ('test_type', models.CharField(max_length=13, verbose_name=b'Test Type', choices=[(b'TOX', b'Toxicity'), (b'DM', b'Disease'), (b'EFF', b'Efficacy'), (b'CC', b'Cell Characterization')])),
            ],
            options={
                'ordering': ('assay_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayModelType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('assay_type_name', models.CharField(unique=True, max_length=200)),
                ('assay_type_description', models.TextField(null=True, blank=True)),
            ],
            options={
                'ordering': ('assay_type_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayPlateTestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('assay_test_time', models.FloatField(null=True, verbose_name=b'Time', blank=True)),
                ('result', models.CharField(default=b'1', max_length=8, verbose_name=b'Pos/Neg?', choices=[(b'0', b'Neg'), (b'1', b'Pos')])),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('value', models.FloatField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayReader',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('reader_name', models.CharField(max_length=128)),
                ('reader_type', models.CharField(max_length=128)),
            ],
            options={
                'ordering': ('reader_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayReadout',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
                ('value', models.FloatField()),
                ('elapsed_time', models.FloatField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('result', models.CharField(default=b'1', max_length=8, verbose_name=b'Pos/Neg?', choices=[(b'0', b'Neg'), (b'1', b'Pos')])),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('value', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayResultFunction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('function_name', models.CharField(unique=True, max_length=100)),
                ('function_results', models.CharField(max_length=100, null=True, blank=True)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('function_name',),
                'verbose_name': 'Function',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayResultType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('assay_result_type', models.CharField(unique=True, max_length=100)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('assay_result_type',),
                'verbose_name': 'Result type',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('toxicity', models.BooleanField(default=False)),
                ('efficacy', models.BooleanField(default=False)),
                ('disease', models.BooleanField(default=False)),
                ('cell_characterization', models.BooleanField(default=False)),
                ('name', models.TextField(default=b'Study-01', help_text=b'Name-###', verbose_name=b'Study Name')),
                ('start_date', models.DateField(help_text=b'YYYY-MM-DD')),
                ('assay_run_id', models.TextField(help_text=b"Standard format 'CenterID-YYYY-MM-DD-Name-###'", unique=True, verbose_name=b'Study ID')),
                ('description', models.TextField(null=True, blank=True)),
                ('file', models.FileField(help_text=b'Do not upload until you have made each Chip Readout', upload_to=b'csv', null=True, verbose_name=b'Batch Data File', blank=True)),
            ],
            options={
                'ordering': ('assay_run_id',),
                'verbose_name': 'Organ Chip Study',
                'verbose_name_plural': 'Organ Chip Studies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayTestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(help_text=b'Reason for why this entry was flagged', max_length=300, null=True, blank=True)),
            ],
            options={
                'verbose_name': 'Chip Result',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayTimepoint',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timepoint', models.FloatField(default=0)),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayWell',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('row', models.CharField(max_length=25)),
                ('column', models.CharField(max_length=25)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AssayWellType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('well_type', models.CharField(unique=True, max_length=200)),
                ('well_description', models.TextField(null=True, blank=True)),
                ('background_color', models.CharField(help_text=b'Provide color code or name. You can pick one from: http://www.w3schools.com/html/html_colornames.asp', max_length=20)),
            ],
            options={
                'ordering': ('well_type',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PhysicalUnits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('unit', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('unit_type', models.CharField(default=b'C', max_length=2, choices=[('V', 'Volume'), ('C', 'Concentration'), ('M', 'Mass'), ('T', 'Time'), ('F', 'Frequency'), ('RA', 'Rate'), ('RE', 'Relative'), ('O', 'Other')])),
            ],
            options={
                'ordering': ['unit_type', 'unit'],
                'verbose_name_plural': 'Physical Units',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ReadoutUnit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('readout_unit', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=512, null=True, blank=True)),
            ],
            options={
                'ordering': ('readout_unit',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(max_length=50)),
                ('study_format', models.CharField(max_length=11, choices=[(b'individual', b'Individual'), (b'integrated', b'Integrated')])),
                ('media_composition', models.CharField(max_length=1000, null=True, blank=True)),
                ('hardware_description', models.CharField(max_length=1000, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StudyModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=1)),
                ('sequence_number', models.IntegerField()),
                ('output', models.CharField(max_length=20, null=True, blank=True)),
                ('integration_mode', models.CharField(max_length=13, choices=[(b'0', b'Not Connected'), (b'1', b'Connected')])),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TimeUnits',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('unit', models.CharField(max_length=16)),
                ('description', models.CharField(max_length=256, null=True, blank=True)),
                ('unit_order', models.FloatField(default=0, verbose_name=b'Seconds')),
                ('created_by', models.ForeignKey(related_name='timeunits_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='timeunits_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='timeunits_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['unit_order'],
                'verbose_name_plural': 'Time Units',
            },
            bases=(models.Model,),
        ),
    ]
