# Generated by Django 5.1.3 on 2025-01-03 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('med', '0027_achievement_userprofile_edited_words_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='achicment_order',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='chenged_order',
            field=models.BooleanField(default=False),
        ),
    ]