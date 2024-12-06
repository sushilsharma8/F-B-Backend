# Generated by Django 5.1.3 on 2024-12-05 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('providers', '0005_serviceproviderprofile_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceproviderprofile',
            name='application_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='serviceproviderprofile',
            name='google_meet_link',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='serviceproviderprofile',
            name='interview_scheduled',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
