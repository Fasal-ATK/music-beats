# Generated by Django 5.0.3 on 2024-06-02 13:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0026_wallet'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon_code',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
