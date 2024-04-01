# Generated by Django 5.0.3 on 2024-04-01 05:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Staff',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('staff_name', models.CharField(unique=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.BigIntegerField(unique=True)),
                ('is_blocked', models.BooleanField()),
            ],
        ),
    ]
