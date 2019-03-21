# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('microdevices', '0007'),
    ]

    operations = [
        migrations.AddField(
            model_name='microphysiologycenter',
            name='contact_email',
            field=models.EmailField(default=b'', max_length=254, blank=True),
        ),
        migrations.AlterField(
            model_name='microphysiologycenter',
            name='groups',
            field=models.ManyToManyField(help_text=b'***PLEASE DO NOT INCLUDE "Admin" OR "Viewer": ONLY SELECT THE BASE GROUP (ie "Taylor_MPS" NOT "Taylor_MPS Admin")***<br>', to='auth.Group'),
        ),
    ]
