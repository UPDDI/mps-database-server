# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cellsamples', '0001_initial'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Manufacturer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('manufacturer_name', models.CharField(max_length=100)),
                ('contact_person', models.CharField(max_length=250, null=True, blank=True)),
                ('Manufacturer_website', models.URLField(null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='manufacturer_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='manufacturer_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='manufacturer_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('manufacturer_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Microdevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('device_name', models.CharField(max_length=200)),
                ('barcode', models.CharField(max_length=200, null=True, verbose_name=b'version/ catalog#', blank=True)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('device_width', models.FloatField(null=True, verbose_name=b'width (mm)', blank=True)),
                ('device_length', models.FloatField(null=True, verbose_name=b'length (mm)', blank=True)),
                ('device_thickness', models.FloatField(null=True, verbose_name=b'thickness (mm)', blank=True)),
                ('device_size_unit', models.CharField(max_length=50, null=True, blank=True)),
                ('device_image', models.ImageField(null=True, upload_to=b'assays', blank=True)),
                ('device_cross_section_image', models.ImageField(null=True, upload_to=b'assays', blank=True)),
                ('device_fluid_volume', models.FloatField(null=True, blank=True)),
                ('device_fluid_volume_unit', models.CharField(max_length=50, null=True, blank=True)),
                ('substrate_thickness', models.FloatField(null=True, verbose_name=b'substrate thickness (um)', blank=True)),
                ('substrate_material', models.CharField(max_length=150, null=True, blank=True)),
            ],
            options={
                'ordering': ('device_name', 'organ'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MicrophysiologyCenter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('center_name', models.CharField(max_length=100)),
                ('center_id', models.CharField(default=b'-', max_length=20)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('contact_person', models.CharField(max_length=250, null=True, blank=True)),
                ('center_website', models.URLField(null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='microphysiologycenter_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('groups', models.ManyToManyField(to='auth.Group')),
                ('modified_by', models.ForeignKey(related_name='microphysiologycenter_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='microphysiologycenter_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('center_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OrganModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('model_name', models.CharField(max_length=200)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('protocol', models.FileField(help_text=b'File detailing the protocols for this model', upload_to=b'protocols', null=True, verbose_name=b'Protocol File', blank=True)),
                ('center', models.ForeignKey(blank=True, to='microdevices.MicrophysiologyCenter', null=True, on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(related_name='organmodel_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('device', models.ForeignKey(blank=True, to='microdevices.Microdevice', null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='organmodel_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('organ', models.ForeignKey(to='cellsamples.Organ', on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='organmodel_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('model_name', 'organ'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ValidatedAssay',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assay', models.ForeignKey(verbose_name=b'Assay Model', to='assays.AssayModel', on_delete=models.CASCADE)),
                ('organ_model', models.ForeignKey(verbose_name=b'Organ Model', to='microdevices.OrganModel', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='microdevice',
            name='center',
            field=models.ForeignKey(blank=True, to='microdevices.MicrophysiologyCenter', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='created_by',
            field=models.ForeignKey(related_name='microdevice_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='manufacturer',
            field=models.ForeignKey(blank=True, to='microdevices.Manufacturer', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='modified_by',
            field=models.ForeignKey(related_name='microdevice_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='organ',
            field=models.ForeignKey(blank=True, to='cellsamples.Organ', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='microdevice',
            name='signed_off_by',
            field=models.ForeignKey(related_name='microdevice_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
