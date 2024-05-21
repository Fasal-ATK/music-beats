# Generated by Django 5.0.3 on 2024-04-14 14:47

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admins', '0002_product_is_listed_alter_category_is_listed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.ImageField(upload_to='product/'), blank=True, size=None),
        ),
    ]