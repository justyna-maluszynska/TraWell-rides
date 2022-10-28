from django.db import models


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=100, null=False)
    last_name = models.CharField(max_length=100, null=False)
    avg_rate = models.DecimalField(max_digits=3, decimal_places=2)
    private = models.BooleanField(null=False, default=True)
    avatar = models.URLField(blank=True, default="")
