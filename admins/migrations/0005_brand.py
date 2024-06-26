# Generated by Django 5.0.3 on 2024-04-23 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admins', '0004_alter_product_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='brand_logo/')),
                ('is_listed', models.BooleanField(default=True)),
            ],
        ),
    ]
