# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assays', '0022'),
    ]

    operations = [
        migrations.AddField(
            model_name='assaychiprawdata',
            name='caution_flag',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='cross_reference',
            field=models.CharField(default=b'', max_length=255),
        ),
        migrations.AddField(
            model_name='assaychiprawdata',
            name='data_upload',
            field=models.ForeignKey(blank=True, to='assays.AssayDataUpload', null=True, on_delete=models.CASCADE),
        ),
    ]
