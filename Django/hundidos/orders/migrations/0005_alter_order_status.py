# Generated by Django 3.2.20 on 2024-11-23 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_alter_order_id_alter_orderproduct_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Pagado', 'Pagado'), ('Pendiente de pago', 'Pendiente de pago')], default='New', max_length=50),
        ),
    ]
