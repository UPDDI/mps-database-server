# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0027'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='assaydatapoint',
            unique_together=set([('matrix_item', 'study_assay', 'sample_location', 'time', 'update_number', 'assay_plate_id', 'assay_well_id', 'replicate', 'subtarget')]),
        ),
    ]
