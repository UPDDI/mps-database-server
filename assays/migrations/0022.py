# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assays', '0021'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayInstance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
        ),
        migrations.CreateModel(
            name='AssayMeasurementType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=2000)),
                ('created_by', models.ForeignKey(related_name='assaymeasurementtype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaymeasurementtype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaymeasurementtype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssayMethod',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=2000)),
                ('protocol_file', models.FileField(null=True, upload_to=b'assays', blank=True)),
                ('created_by', models.ForeignKey(related_name='assaymethod_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('measurement_type', models.ForeignKey(to='assays.AssayMeasurementType', on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaymethod_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaymethod_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssaySampleLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=2000)),
                ('created_by', models.ForeignKey(related_name='assaysamplelocation_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaysamplelocation_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaysamplelocation_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssaySupplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=2000)),
                ('created_by', models.ForeignKey(related_name='assaysupplier_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaysupplier_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaysupplier_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AssayTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=512)),
                ('description', models.CharField(max_length=2000)),
                ('short_name', models.CharField(unique=True, max_length=20)),
                ('created_by', models.ForeignKey(related_name='assaytarget_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='assaytarget_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='assaytarget_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='assay_plate_id',
            field=models.CharField(default=b'N/A', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='assay_well_id',
            field=models.CharField(default=b'N/A', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='replicate',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='time',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='assaychiprawdata',
            name='assay_id',
            field=models.ForeignKey(blank=True, to='assays.AssayChipReadoutAssay', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaychiprawdata',
            name='elapsed_time',
            field=models.FloatField(default=0, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychiprawdata',
            name='field_id',
            field=models.CharField(default=b'0', max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadoutassay',
            name='assay_id',
            field=models.ForeignKey(verbose_name=b'Assay', blank=True, to='assays.AssayModel', null=True, on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaychipreadoutassay',
            name='object_type',
            field=models.CharField(default=b'F', max_length=6, verbose_name=b'Object of Interest', blank=True, choices=[(b'F', b'Field'), (b'C', b'Colony'), (b'M', b'Media'), (b'X', b'Other')]),
        ),
        migrations.AlterField(
            model_name='assaychipreadoutassay',
            name='reader_id',
            field=models.ForeignKey(verbose_name=b'Reader', blank=True, to='assays.AssayReader', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assaymethod',
            name='supplier',
            field=models.ForeignKey(blank=True, to='assays.AssaySupplier', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assayinstance',
            name='method',
            field=models.ForeignKey(to='assays.AssayMethod', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assayinstance',
            name='study',
            field=models.ForeignKey(to='assays.AssayRun', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assayinstance',
            name='target',
            field=models.ForeignKey(to='assays.AssayTarget', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assayinstance',
            name='unit',
            field=models.ForeignKey(to='assays.PhysicalUnits', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='assay_instance',
            field=models.ForeignKey(blank=True, to='assays.AssayInstance', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='sample_location',
            field=models.ForeignKey(blank=True, to='assays.AssaySampleLocation', null=True, on_delete=models.CASCADE),
        ),
    ]
