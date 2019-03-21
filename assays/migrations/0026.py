# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assays', '0025'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssayRunStakeholder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('signed_off_date', models.DateTimeField(null=True, blank=True)),
                ('signed_off_notes', models.CharField(default=b'', max_length=255, blank=True)),
                ('sign_off_required', models.BooleanField(default=True)),
                ('group', models.ForeignKey(to='auth.Group', on_delete=models.CASCADE)),
                ('signed_off_by', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='assayrun',
            name='signed_off_notes',
            field=models.CharField(default=b'', max_length=255, blank=True),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaychipreadout',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaychipsetup',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assaychiptestresult',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaychiptestresult',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assaydataupload',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaydataupload',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assaylayout',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assaylayout',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assayplatereadout',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assayplatesetup',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assayplatetestresult',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assayplatetestresult',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='access_groups',
            field=models.ManyToManyField(help_text=b'Level 2 Access Groups Assignation', related_name='access_groups', to='auth.Group', blank=True),
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='group',
            field=models.ForeignKey(help_text=b'Bind to a group (Level 0)', to='auth.Group', on_delete=models.CASCADE),
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='restricted',
            field=models.BooleanField(default=True, help_text=b'Check box to restrict to selected group. Unchecked sends to Level 3'),
        ),
        migrations.AlterField(
            model_name='assayrun',
            name='use_in_calculations',
            field=models.BooleanField(default=False, help_text=b'Set this to True if this data should be included in Compound Reports and other data aggregations.'),
        ),
        migrations.AddField(
            model_name='assayrunstakeholder',
            name='study',
            field=models.ForeignKey(to='assays.AssayRun', on_delete=models.CASCADE),
        ),
    ]
