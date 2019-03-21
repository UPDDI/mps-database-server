# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cellsamples', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdverseEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CompoundAdverseEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('frequency', models.IntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DrugTrial',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('title', models.CharField(max_length=255, null=True, blank=True)),
                ('condition', models.CharField(max_length=1400, null=True, blank=True)),
                ('figure1', models.ImageField(null=True, upload_to=b'figures', blank=True)),
                ('figure2', models.ImageField(null=True, upload_to=b'figures', blank=True)),
                ('gender', models.CharField(default=b'U', max_length=1, null=True, blank=True, choices=[(b'F', b'female'), (b'M', b'male'), (b'X', b'mixed'), (b'U', b'unknown or unspecified')])),
                ('population_size', models.CharField(default=b'1', max_length=50, null=True, blank=True)),
                ('age_average', models.FloatField(null=True, blank=True)),
                ('age_max', models.FloatField(null=True, blank=True)),
                ('age_min', models.FloatField(null=True, blank=True)),
                ('age_unit', models.CharField(default=b'Y', max_length=1, null=True, blank=True, choices=[(b'M', b'months'), (b'Y', b'years')])),
                ('weight_average', models.FloatField(null=True, blank=True)),
                ('weight_max', models.FloatField(null=True, blank=True)),
                ('weight_min', models.FloatField(null=True, blank=True)),
                ('weight_unit', models.CharField(default=b'L', max_length=1, null=True, blank=True, choices=[(b'K', b'kilograms'), (b'L', b'pounds')])),
                ('trial_type', models.CharField(max_length=1, choices=[(b'S', b'Microphysiology'), (b'P', b'Preclinical'), (b'C', b'Clinical'), (b'M', b'Post-marketing'), (b'B', b'Combined Clinical-Post Market'), (b'U', b'Unknown / Unspecified')])),
                ('trial_sub_type', models.CharField(default=b'C', max_length=1, choices=[(b'C', b'Case Report'), (b'P', b'Population Report'), (b'U', b'Unknown / Unspecified')])),
                ('trial_date', models.DateField(null=True, blank=True)),
                ('description', models.CharField(max_length=1400, null=True, blank=True)),
                ('source_link', models.URLField(null=True, blank=True)),
                ('references', models.CharField(max_length=400, null=True, verbose_name=b'Trial ID/Reference')),
            ],
            options={
                'ordering': ('compound', 'species'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Finding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('finding_name', models.CharField(max_length=100)),
                ('finding_unit', models.CharField(max_length=40, null=True, blank=True)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
            ],
            options={
                'ordering': ('organ', 'finding_type', 'finding_name'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FindingResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('finding_time', models.FloatField(null=True, verbose_name=b'Time', blank=True)),
                ('result', models.CharField(default=b'1', max_length=8, verbose_name=b'Pos/Neg?', choices=[(b'0', b'Neg'), (b'1', b'Pos')])),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('percent_min', models.FloatField(null=True, verbose_name=b'Min Affected (% Population)', blank=True)),
                ('percent_max', models.FloatField(null=True, verbose_name=b'Max Affected (% Population)', blank=True)),
                ('frequency', models.CharField(blank=True, max_length=25, null=True, choices=[(b'>= 10%', b'>= 10% : Very Common'), (b'1 - < 10%', b'1 - < 10% : Common'), (b'0.1 - < 1%', b'0.1 - < 1% : Uncommon'), (b'0.01 - < 0.1%', b'0.01 - < 0.1% : Rare'), (b'< 0.01%', b'< 0.01% : Very Rare')])),
                ('value', models.FloatField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FindingType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('finding_type', models.CharField(unique=True, max_length=100)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
            ],
            options={
                'ordering': ('finding_type',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='OpenFDACompound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('warnings', models.TextField(null=True, blank=True)),
                ('black_box', models.BooleanField(default=False)),
                ('nonclinical_toxicology', models.TextField(null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResultDescriptor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('result_descriptor', models.CharField(unique=True, max_length=40)),
            ],
            options={
                'ordering': ('result_descriptor',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Species',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('species_name', models.CharField(unique=True, max_length=40)),
            ],
            options={
                'ordering': ('species_name',),
                'verbose_name_plural': 'species',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Test',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('test_name', models.CharField(max_length=40, verbose_name=b'Organ Function Test')),
                ('test_unit', models.CharField(max_length=40, null=True, blank=True)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='test_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='test_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('organ', models.ForeignKey(blank=True, to='cellsamples.Organ', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('test_name', 'organ', 'test_type'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('test_time', models.FloatField(null=True, verbose_name=b'Time', blank=True)),
                ('result', models.CharField(default=b'1', choices=[(b'0', b'Neg'), (b'1', b'Pos')], max_length=8, blank=True, null=True, verbose_name=b'Pos/Neg?')),
                ('severity', models.CharField(default=b'-1', choices=[(b'-1', b'UNKNOWN'), (b'0', b'NEGATIVE'), (b'1', b'+'), (b'2', b'+ +'), (b'3', b'+ + +'), (b'4', b'+ + + +'), (b'5', b'+ + + + +')], max_length=5, blank=True, null=True, verbose_name=b'Severity')),
                ('percent_min', models.FloatField(null=True, verbose_name=b'Min Affected (% Population)', blank=True)),
                ('percent_max', models.FloatField(null=True, verbose_name=b'Max Affected (% Population)', blank=True)),
                ('value', models.FloatField(null=True, blank=True)),
                ('descriptor', models.ForeignKey(blank=True, to='drugtrials.ResultDescriptor', null=True, on_delete=models.CASCADE)),
                ('drug_trial', models.ForeignKey(to='drugtrials.DrugTrial', on_delete=models.CASCADE)),
                ('test_name', models.ForeignKey(verbose_name=b'Test', blank=True, to='drugtrials.Test', null=True, on_delete=models.CASCADE)),
                ('time_units', models.ForeignKey(blank=True, to='assays.TimeUnits', null=True, on_delete=models.CASCADE)),
                ('value_units', models.ForeignKey(blank=True, to='assays.PhysicalUnits', null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TestType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('test_type', models.CharField(unique=True, max_length=60)),
                ('description', models.CharField(max_length=200, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='testtype_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='testtype_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='testtype_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('test_type',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TrialSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('source_name', models.CharField(unique=True, max_length=40)),
                ('source_website', models.URLField(null=True, blank=True)),
                ('description', models.CharField(max_length=400, null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='trialsource_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='trialsource_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='trialsource_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('source_name',),
            },
            bases=(models.Model,),
        ),
    ]
