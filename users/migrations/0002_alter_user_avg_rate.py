# Generated by Django 4.1.1 on 2022-10-12 17:08

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_init_models'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avg_rate',
            field=models.DecimalField(decimal_places=2, max_digits=3),
        ),
    ]
