# Generated by Django 5.0.3 on 2024-05-18 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0014_remove_address_is_default_orderaddress'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderaddress',
            name='name',
            field=models.CharField(max_length=25, null=True),
        ),
    ]