# sensor_data/urls.py
from django.urls import path
from .views import dashboard, SensorDataView, LatestSensorDataView

urlpatterns = [
   path('sensor-data/', SensorDataView.as_view(), name='sensor_data_api'),
   path('latest-sensor-data/', LatestSensorDataView.as_view(), name='latest_sensor_data_api'),
   path('dashboard/', dashboard, name='dashboard')

]

