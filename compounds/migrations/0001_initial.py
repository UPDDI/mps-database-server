# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Compound',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True, null=True)),
                ('modified_on', models.DateTimeField(auto_now=True, null=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('locked', models.BooleanField(default=False, help_text=b'Check the box and save to lock the entry. Uncheck and save to enable editing.')),
                ('name', models.CharField(help_text=b'Preferred compound name.', unique=True, max_length=200)),
                ('synonyms', models.TextField(max_length=4000, null=True, blank=True)),
                ('chemblid', models.CharField(help_text=b'Enter a ChEMBL id, e.g. CHEMBL25, and click Retrieve to get compound information automatically.', max_length=20, null=True, verbose_name=b'ChEMBL ID', blank=True)),
                ('pubchemid', models.CharField(max_length=40, null=True, verbose_name=b'PubChem ID', blank=True)),
                ('inchikey', models.CharField(help_text=b'IUPAC standard InChI key for the compound', max_length=27, null=True, verbose_name=b'InChI key', blank=True)),
                ('smiles', models.CharField(help_text=b'Canonical smiles, generated using pipeline pilot.', max_length=1000, null=True, blank=True)),
                ('molecular_formula', models.CharField(help_text=b'Molecular formula of compound.', max_length=40, null=True, blank=True)),
                ('molecular_weight', models.FloatField(help_text=b'Molecular weight of the compound', null=True, blank=True)),
                ('rotatable_bonds', models.IntegerField(help_text=b'Number of rotatable bonds.', null=True, blank=True)),
                ('acidic_pka', models.FloatField(help_text=b'The most acidic pKa calculated using ACDlabs.', null=True, verbose_name=b'Acidic pKa', blank=True)),
                ('basic_pka', models.FloatField(help_text=b'The most basic pKa calculated using ACDlabs.', null=True, verbose_name=b'Basic pKa', blank=True)),
                ('logp', models.FloatField(help_text=b'The calculated octanol/water partition coefficient using ACDlabs', null=True, verbose_name=b'LogP', blank=True)),
                ('logd', models.FloatField(help_text=b'The calculated octanol/water distribution coefficient at pH7.4 using ACDlabs.', null=True, verbose_name=b'LogD', blank=True)),
                ('alogp', models.FloatField(help_text=b'Calculated ALogP.', null=True, verbose_name=b'ALogP', blank=True)),
                ('known_drug', models.BooleanField(default=False, verbose_name=b'Known drug?')),
                ('medchem_friendly', models.BooleanField(default=False, verbose_name=b'Med Chem friendly?')),
                ('ro5_violations', models.IntegerField(help_text=b"Number of properties defined in Lipinski's Rule of 5 (RO5) that the compound fails.", null=True, verbose_name=b'Rule of 5 violations', blank=True)),
                ('ro3_passes', models.BooleanField(default=False, help_text=b'Rule of 3 passes.  It is suggested that compounds that pass all these criteria aremore likely to be hits in fragment screening.', verbose_name=b'Passes rule of 3?')),
                ('species', models.CharField(help_text=b'A description of the predominant species occurring at pH 7.4 and can be acid, base, neutral or zwitterion.', max_length=10, null=True, verbose_name=b'Molecular species', blank=True)),
                ('last_update', models.DateField(help_text=b'Last time when activities associated with the compound were updated.', null=True, blank=True)),
                ('created_by', models.ForeignKey(related_name='compound_created_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('modified_by', models.ForeignKey(related_name='compound_modified_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(related_name='compound_signed_off_by', blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
    ]
