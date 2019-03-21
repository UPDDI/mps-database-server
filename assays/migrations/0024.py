# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0023'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assaychipresult',
            name='assay_name',
            field=models.ForeignKey(verbose_name=b'Assay', to='assays.AssayInstance', on_delete=models.CASCADE),
        ),
    ]
