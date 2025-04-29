# sensor_data/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
class CustomUser(AbstractUser):
    token = models.CharField(max_length=17, unique=True, null=False, blank=False)  # Store MAC address (Token)

    def __str__(self):
        return self.username


class SensorData(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sensor_data')
    node = models.IntegerField()
    temperature = models.FloatField()
    smoke = models.FloatField()
    flame = models.BooleanField()
    humidity = models.FloatField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sensor Data at {self.timestamp} for user {self.user.username} of node{self.node}"
    


