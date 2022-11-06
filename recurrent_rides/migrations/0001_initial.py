# Generated by Django 4.1.1 on 2022-11-05 13:39

import datetime
import django.contrib.postgres.fields
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cities', '0003_alter_city_lat_alter_city_lng'),
        ('vehicles', '0004_alter_vehicle_user'),
        ('users', '0007_alter_user_email'),
    ]

    operations = [
        migrations.CreateModel(
            name='RecurrentRide',
            fields=[
                ('ride_id', models.AutoField(primary_key=True, serialize=False)),
                ('area_from', models.CharField(blank=True, default='', max_length=100)),
                ('area_to', models.CharField(blank=True, default='', max_length=100)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('frequency_type', models.CharField(choices=[('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='daily', max_length=9)),
                ('frequence', models.IntegerField(default=1)),
                ('occurrences', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('MON', 'Monday'), ('TUE', 'Tuesday'), ('WED', 'Wednesday'), ('THU', 'Thursday'), ('FRI', 'Friday'), ('SAT', 'Saturday'), ('SUN', 'Sunday')], max_length=10), blank=True, null=True, size=None)),
                ('duration', models.DurationField(default=datetime.timedelta)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('seats', models.PositiveIntegerField()),
                ('automatic_confirm', models.BooleanField(default=False)),
                ('description', models.TextField(blank=True, default='')),
                ('is_cancelled', models.BooleanField(default=False)),
                ('city_from', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recur_city_from', to='cities.city')),
                ('city_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recur_city_to', to='cities.city')),
                ('driver', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='users.user')),
                ('vehicle', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='vehicles.vehicle')),
            ],
        ),
    ]