# Generated by Django 5.0.3 on 2024-06-06 06:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0028_order_reason_alter_order_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('order_placed', 'Order Placed'), ('shipped', 'Shipped'), ('out_for_delivery', 'Out for Delivery'), ('completed', 'Completed'), ('canceled', 'Canceled'), ('return_requested', 'Return Requested'), ('return_accepted', 'Return Accepted'), ('return_rejected', 'Return Rejected'), ('returned', 'Returned')], default='order_placed', max_length=20),
        ),
    ]
