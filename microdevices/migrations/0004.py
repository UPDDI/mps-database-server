# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0003'),
    ]

    operations = [
        migrations.AddField(
            model_name='organmodel',
            name='model_image',
            field=models.ImageField(null=True, upload_to=b'models', blank=True),
        ),
    ]
