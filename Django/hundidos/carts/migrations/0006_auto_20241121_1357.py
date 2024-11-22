# Generated by Django 3.2.20 on 2024-11-21 12:57

import carts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0005_alter_cart_id_alter_cartitem_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cartitem',
            name='quantity',
        ),
        migrations.AddField(
            model_name='cartitem',
            name='fecha_fin',
            field=models.DateField(default=carts.models.get_default_end_date),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='fecha_inicio',
            field=models.DateField(default=carts.models.get_default_start_date),
        ),
    ]
