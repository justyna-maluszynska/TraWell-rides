# Generated by Django 4.1.1 on 2022-10-18 17:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_alter_user_avatar'),
        ('vehicles', '0001_init_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehicle',
            name='user_id',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, related_name='vehicles', to='users.user'),
        ),
    ]
