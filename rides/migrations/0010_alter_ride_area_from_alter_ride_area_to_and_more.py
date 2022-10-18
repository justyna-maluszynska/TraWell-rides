# Generated by Django 4.1.1 on 2022-10-17 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0009_alter_ride_available_seats'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ride',
            name='area_from',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='ride',
            name='area_to',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='ride',
            name='description',
            field=models.TextField(blank=True, default=''),
        ),
    ]