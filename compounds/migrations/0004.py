# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compounds', '0003'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompoundTarget',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=150)),
                ('uniprot_id', models.CharField(max_length=20, null=True, blank=True)),
                ('action', models.CharField(max_length=75)),
                ('pharmacological_action', models.CharField(max_length=20)),
                ('organism', models.CharField(max_length=150)),
                ('type', models.CharField(max_length=30)),
            ],
        ),
        migrations.AddField(
            model_name='compound',
            name='absorption',
            field=models.CharField(default=b'', help_text=b'Absorption Description from DrugBank', max_length=1000, verbose_name=b'Absorption', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='bioavailability',
            field=models.CharField(default=b'', help_text=b'Bioavailability from DrugBank', max_length=20, verbose_name=b'Bioavailability', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='clearance',
            field=models.CharField(default=b'', help_text=b'Clearance from DrugBank', max_length=500, verbose_name=b'Clearance', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='clinical',
            field=models.CharField(default=b'', help_text=b'Summary of clinical findings', max_length=1000, verbose_name=b'Clinical Findings', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='drug_class',
            field=models.CharField(default=b'', help_text=b'Drug Class from DrugBank', max_length=150, verbose_name=b'Class', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='drugbank_id',
            field=models.CharField(default=b'', help_text=b'DrugBank ID', max_length=20, verbose_name=b'DrugBank ID', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='half_life',
            field=models.CharField(default=b'', help_text=b'Half Life from DrugBank', max_length=100, verbose_name=b'Half Life', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='pk_metabolism',
            field=models.CharField(default=b'', help_text=b'Summary of pharmacokinetics and metabolism', max_length=1000, verbose_name=b'PK/Metabolism', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='post_marketing',
            field=models.CharField(default=b'', help_text=b'Summary of post-marketing findings', max_length=1000, verbose_name=b'Post-marketing', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='preclinical',
            field=models.CharField(default=b'', help_text=b'Summary of pre-clinical findings', max_length=1000, verbose_name=b'Pre-clinical Findings', blank=True),
        ),
        migrations.AddField(
            model_name='compound',
            name='protein_binding',
            field=models.CharField(default=b'', help_text=b'Protein Binding from DrugBank', max_length=20, verbose_name=b'Protein Binding', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='acidic_pka',
            field=models.FloatField(help_text=b'The most acidic pKa calculated using ACDlabs.', null=True, verbose_name=b'Acidic pKa (ACD)', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='basic_pka',
            field=models.FloatField(help_text=b'The most basic pKa calculated using ACDlabs.', null=True, verbose_name=b'Basic pKa (ACD)', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='chemblid',
            field=models.CharField(default=b'', help_text=b'Enter a ChEMBL id, e.g. CHEMBL25, and click Retrieve to get compound information automatically.', max_length=20, verbose_name=b'ChEMBL ID', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='inchikey',
            field=models.CharField(default=b'', help_text=b'IUPAC standard InChI key for the compound', max_length=27, verbose_name=b'InChI key', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='logd',
            field=models.FloatField(help_text=b'The calculated octanol/water distribution coefficient at pH7.4 using ACDlabs.', null=True, verbose_name=b'LogD (ACD)', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='logp',
            field=models.FloatField(help_text=b'The calculated octanol/water partition coefficient using ACDlabs', null=True, verbose_name=b'LogP (ACD)', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='molecular_formula',
            field=models.CharField(default=b'', help_text=b'Molecular formula of compound.', max_length=40, blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='pubchemid',
            field=models.CharField(default=b'', max_length=40, verbose_name=b'PubChem ID', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='smiles',
            field=models.CharField(default=b'', help_text=b'Canonical smiles, generated using pipeline pilot.', max_length=1000, blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='species',
            field=models.CharField(default=b'', help_text=b'A description of the predominant species occurring at pH 7.4 and can be acid, base, neutral or zwitterion.', max_length=10, verbose_name=b'Molecular species', blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='synonyms',
            field=models.TextField(default=b'', max_length=4000, blank=True),
        ),
        migrations.AlterField(
            model_name='compound',
            name='tags',
            field=models.TextField(default=b'', help_text=b'Tags for the compound (EPA, NCATS, etc.)', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='compoundproperty',
            unique_together=set([]),
        ),
        migrations.AddField(
            model_name='compoundtarget',
            name='compound',
            field=models.ForeignKey(to='compounds.Compound', on_delete=models.CASCADE),
        ),
    ]
