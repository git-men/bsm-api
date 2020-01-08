# Generated by Django 2.1.3 on 2020-01-02 08:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api_db', '0010_trigger_triggeraction_triggeractionfilter_triggeractionset_triggerfilter'),
    ]

    operations = [
        migrations.AddField(
            model_name='triggeractionfilter',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api_db.TriggerActionFilter', verbose_name='parent'),
        ),
    ]
