# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings
import assays.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('auth', '0006_require_contenttypes_0002'),
        ('compounds', '0009'),
        ('assays', '0020'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayCompoundInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('concentration', models.FloatField()),
                ('addition_time', models.FloatField(blank=True)),
                ('duration', models.FloatField(blank=True)),
                ('chip_setup', models.ForeignKey(blank=True, to='assays.AssayChipSetup', null=True, on_delete=models.CASCADE)),
                ('compound_instance', models.ForeignKey(blank=True, to='compounds.CompoundInstance', null=True, on_delete=models.CASCADE)),
                ('concentration_unit', models.ForeignKey(verbose_name=b'Concentration Unit', to='assays.PhysicalUnits', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='AssayDataUpload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('flagged', models.BooleanField(default=False, help_text=b'Check box to flag for review')),
                ('reason_for_flag', models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True)),
                ('file_location', models.URLField(null=True, blank=True)),
                ('chip_readout', models.ManyToManyField(to='assays.AssayChipReadout')),
                ('created_by', models.ForeignKey(related_name='assaydataupload_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('group', models.ForeignKey(help_text=b'Bind to a group', to='auth.Group', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaydataupload_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('plate_readout', models.ManyToManyField(to='assays.AssayPlateReadout')),
                ('signed_off_by', models.ForeignKey(related_name='assaydataupload_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssayQualityIndicator',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=255)),
                ('code', models.CharField(unique=True, max_length=10)),
                ('description', models.CharField(max_length=2000)),
                ('created_by', models.ForeignKey(related_name='assayqualityindicator_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assayqualityindicator_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assayqualityindicator_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='notes',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='update_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='assayreadout',
            name='notes',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='assayreadout',
            name='update_number',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='assayrun',
            name='bulk_file',
            field=models.FileField(upload_to=assays.models.bulk_readout_file_location, null=True, verbose_name=b'Data File', blank=True),
        ),
        migrations.AlterField(
            model_name='assaylayout',
            name='layout_name',
            field=models.CharField(unique=True, max_length=200),
        ),
        migrations.AlterField(
            model_name='assaywellcompound',
            name='compound',
            field=models.ForeignKey(blank=True, to='compounds.Compound', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaywellcompound',
            name='concentration',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='assaywellcompound',
            name='concentration_unit',
            field=models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='assaychipreadoutassay',
            unique_together=set([('readout_id', 'assay_id', 'readout_unit')]),
        ),
        migrations.AddField(
            model_name='assaydataupload',
            name='study',
            field=models.ForeignKey(to='assays.AssayRun', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assaywellcompound',
            name='assay_compound_instance',
            field=models.ForeignKey(blank=True, to='assays.AssayCompoundInstance', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterUniqueTogether(
            name='assaycompoundinstance',
            unique_together=set([('chip_setup', 'compound_instance', 'concentration', 'concentration_unit', 'addition_time', 'duration')]),
        ),
    ]
