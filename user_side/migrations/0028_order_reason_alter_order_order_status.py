# Generated by Django 5.0.3 on 2024-06-05 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0027_order_coupon_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='reason',
            field=models.CharField(blank=True, choices=[('damaged_product', 'Damaged Product'), ('poor_quality', 'Poor Quality'), ('different_product', 'Different Product'), ('something_else', 'Something Else')], max_length=20),
        ),
        migrations.AlterField(
            model_name='order',
            name='order_status',
            field=models.CharField(choices=[('order_placed', 'Order Placed'), ('shipped', 'Shipped'), ('out_for_delivery', 'Out for Delivery'), ('completed', 'Completed'), ('canceled', 'Canceled'), ('return_requested', 'Return Requested'), ('return_rejected', 'Return Rejected'), ('returned', 'Returned')], default='order_placed', max_length=20),
        ),
    ]
