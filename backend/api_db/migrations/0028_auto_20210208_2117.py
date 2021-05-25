# Generated by Django 2.2.17 on 2021-02-08 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_db', '0027_remove_function_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='functionparameter',
            name='display_name',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='显示名'),
        ),
        migrations.AlterField(
            model_name='functionparameter',
            name='type',
            field=models.CharField(choices=[('string', '字符串'), ('integer', '整数'), ('decimal', '浮点数'), ('boolean', '布尔值'), ('ref', '数据')], max_length=20, verbose_name='类型'),
        ),
    ]