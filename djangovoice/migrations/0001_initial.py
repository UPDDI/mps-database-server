# -*- coding: utf-8 -*-


from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500, verbose_name='Title')),
                ('description', models.TextField(blank=True, help_text='This will be viewable by other people - do not include any private details such as passwords or phone numbers here.', verbose_name='Description')),
                ('anonymous', models.BooleanField(default=False, help_text='Do not show who sent this', verbose_name='Anonymous')),
                ('private', models.BooleanField(default=False, help_text='Hide from public pages. Only site administrators will be able to view and respond to this', verbose_name='Private')),
                ('email', models.EmailField(blank=True, help_text='You must provide your e-mail so we can answer you. Alternatively you can bookmark next page and check out for an answer later.', max_length=254, null=True, verbose_name='E-mail')),
                ('slug', models.SlugField(blank=True, max_length=10, null=True)),
                ('created', models.DateTimeField(auto_now_add=True, null=True)),
                ('duplicate', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='djangovoice.Feedback', verbose_name='Duplicate')),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
                'verbose_name': 'feedback',
                'verbose_name_plural': 'feedback',
            },
        ),
        migrations.CreateModel(
            name='FeedbackVote',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=1, verbose_name='value')),
                ('date', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='voted on')),
                ('object', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='djangovoice.Feedback', verbose_name='object')),
                ('voter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='voter')),
            ],
            options={
                'ordering': ('date',),
                'verbose_name': 'Vote',
                'verbose_name_plural': 'Votes',
            },
        ),
        migrations.CreateModel(
            name='Status',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('slug', models.SlugField(max_length=500)),
                ('default', models.BooleanField(default=False, help_text='New feedback will have this status')),
                ('status', models.CharField(choices=[(b'open', 'Open'), (b'closed', 'Closed')], default=b'open', max_length=10)),
            ],
            options={
                'verbose_name': 'status',
                'verbose_name_plural': 'statuses',
            },
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=500)),
                ('slug', models.SlugField(max_length=500)),
            ],
        ),
        migrations.AddField(
            model_name='feedback',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='djangovoice.Status', verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='feedback',
            name='type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='djangovoice.Type', verbose_name='Type'),
        ),
        migrations.AddField(
            model_name='feedback',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
        migrations.AlterUniqueTogether(
            name='feedbackvote',
            unique_together=set([('voter', 'object')]),
        ),
    ]
