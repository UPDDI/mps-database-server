# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cellsamples', '0003'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cellsample',
            name='cell_source',
            field=models.CharField(default=b'Primary', max_length=20, blank=True, choices=[(b'Freshly isolated', b'Freshly isolated'), (b'Cryopreserved', b'Cryopreserved'), (b'Cultured', b'Cultured'), (b'Other', b'Other')]),
        ),
        migrations.AlterField(
            model_name='cellsample',
            name='reason_for_flag',
            field=models.CharField(default=b'', help_text=b'Reason for why this entry was flagged', max_length=300, blank=True),
        ),
        migrations.AlterField(
            model_name='celltype',
            name='species',
            field=models.CharField(default=b'Human', max_length=10, blank=True, choices=[(b'Human', b'Human'), (b'Rat', b'Rat'), (b'Mouse', b'Mouse')]),
        ),
    ]
