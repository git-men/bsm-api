# Generated by Django 2.1.3 on 2020-01-13 09:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_db', '0015_auto_20200113_1640'),
    ]

    operations = [
        migrations.AlterField(
            model_name='triggeraction',
            name='action',
            field=models.CharField(choices=[('create', '创建记录'), ('update', '更新记录'), ('delete', '删除记录')], max_length=20, verbose_name='条件类型'),
        ),
    ]
