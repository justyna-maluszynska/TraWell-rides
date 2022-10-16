# Generated by Django 4.1.1 on 2022-10-16 16:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_avatar'),
        ('rides', '0007_alter_ride_area_from_alter_ride_area_to_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='participation',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='passenger', to='users.user'),
        ),
        migrations.AlterField(
            model_name='ride',
            name='passengers',
            field=models.ManyToManyField(blank=True, through='rides.Participation', to='users.user'),
        ),
    ]