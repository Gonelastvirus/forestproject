"""
URL configuration for forestfire project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# forestfire/urls.py
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from sensor_data import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
     path("logout/", views.logout_view, name="logout"),
    path('', lambda request: redirect('login/')),
    path('admin/', admin.site.urls),
    path('api/', include('sensor_data.urls')),  # New: Separate API routes
    path('dashboard/', views.dashboard, name='dashboard'),  # Clean dashboard path
    path('settings/', views.user_settings, name='user_settings'),
   path('data-visualization/', views.sensor_data_visualization, name='sensor_data_visualization'),
]
