# Generated by Django 3.2.20 on 2024-11-24 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0008_auto_20241117_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='fabricante',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='puerto',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='stock',
            field=models.IntegerField(default=1),
        ),
    ]