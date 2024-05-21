# Generated by Django 5.0.3 on 2024-04-30 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0004_address'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='address_line2',
            new_name='address_line',
        ),
        migrations.RemoveField(
            model_name='address',
            name='address_line1',
        ),
        migrations.AddField(
            model_name='address',
            name='name',
            field=models.CharField(max_length=25, null=True),
        ),
    ]