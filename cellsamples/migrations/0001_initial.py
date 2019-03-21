# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Biosensor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=255)),
                ('product_id', models.CharField(max_length=255, blank=True)),
                ('lot_number', models.CharField(max_length=255, verbose_name=b'Lot#', blank=True)),
                ('description', models.CharField(max_length=512, blank=True)),
                ('created_by', models.ForeignKey(related_name='biosensor_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='biosensor_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='biosensor_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CellSample',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('restricted', models.BooleanField(default=True, help_text=b'Check box to restrict to selected group')),
                ('cell_source', models.CharField(default=b'Primary', max_length=20, null=True, blank=True, choices=[(b'Freshly isolated', b'Freshly isolated'), (b'Cryopreserved', b'Cryopreserved'), (b'Cultured', b'Cultured'), (b'Other', b'Other')])),
                ('notes', models.TextField(blank=True)),
                ('receipt_date', models.DateField()),
                ('barcode', models.CharField(max_length=255, verbose_name=b'Barcode/Lot#', blank=True)),
                ('product_id', models.CharField(max_length=255, blank=True)),
                ('patient_age', models.IntegerField(null=True, blank=True)),
                ('patient_gender', models.CharField(default=b'N', max_length=1, blank=True, choices=[(b'N', b'Not-specified'), (b'F', b'Female'), (b'M', b'Male')])),
                ('patient_condition', models.CharField(max_length=255, blank=True)),
                ('isolation_datetime', models.DateField(null=True, verbose_name=b'Isolation', blank=True)),
                ('isolation_method', models.CharField(max_length=255, verbose_name=b'Method', blank=True)),
                ('isolation_notes', models.CharField(max_length=255, verbose_name=b'Notes', blank=True)),
                ('viable_count', models.FloatField(null=True, blank=True)),
                ('viable_count_unit', models.CharField(default=b'N', max_length=1, blank=True, choices=[(b'N', b'Not-specified'), (b'A', b'per area'), (b'V', b'per volume')])),
                ('percent_viability', models.FloatField(null=True, blank=True)),
                ('cell_image', models.ImageField(null=True, upload_to=b'cellsamples', blank=True)),
            ],
            options={
                'ordering': ('cell_type', 'cell_source', 'supplier', 'barcode', 'id'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CellSubtype',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('cell_subtype', models.CharField(help_text=b'Example: motor (type of neuron), skeletal (type of muscle), etc.', unique=True, max_length=255)),
                ('created_by', models.ForeignKey(related_name='cellsubtype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='cellsubtype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='cellsubtype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('cell_subtype',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CellType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('cell_type', models.CharField(help_text=b'Example: hepatocyte, muscle, kidney, etc', max_length=255)),
                ('species', models.CharField(default=b'Human', max_length=10, null=True, blank=True, choices=[(b'Human', b'Human'), (b'Rat', b'Rat')])),
                ('cell_subtype', models.ForeignKey(to='cellsamples.CellSubtype', on_delete=models.CASCADE)),
                ('created_by', models.ForeignKey(related_name='celltype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='celltype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('species', 'cell_type', 'cell_subtype'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Organ',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('organ_name', models.CharField(unique=True, max_length=255)),
                ('created_by', models.ForeignKey(related_name='organ_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='organ_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='organ_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('organ_name',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(unique=True, max_length=255)),
                ('phone', models.CharField(max_length=255, blank=True)),
                ('address', models.CharField(max_length=255, blank=True)),
                ('created_by', models.ForeignKey(related_name='supplier_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='supplier_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='supplier_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='celltype',
            name='organ',
            field=models.ForeignKey(to='cellsamples.Organ', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='celltype',
            name='signed_off_by',
            field=models.ForeignKey(related_name='celltype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='celltype',
            unique_together=set([('cell_type', 'species', 'cell_subtype')]),
        ),
        migrations.AddField(
            model_name='cellsample',
            name='cell_type',
            field=models.ForeignKey(to='cellsamples.CellType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='created_by',
            field=models.ForeignKey(related_name='cellsample_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group', to='auth.Group', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='modified_by',
            field=models.ForeignKey(related_name='cellsample_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='signed_off_by',
            field=models.ForeignKey(related_name='cellsample_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='cellsample',
            name='supplier',
            field=models.ForeignKey(to='cellsamples.Supplier', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='biosensor',
            name='supplier',
            field=models.ForeignKey(to='cellsamples.Supplier', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
