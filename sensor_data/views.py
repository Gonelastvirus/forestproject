# sensor_data/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.shortcuts import render, redirect
from .models import SensorData, CustomUser
from .serializers import SensorDataSerializer
from django.contrib.auth.decorators import login_required
from django.db.models import Max

# API view to receive sensor data
class SensorDataView(APIView):
    def post(self, request):
        token = request.data.get('token')  # Extract token from the data
        user = CustomUser.objects.filter(token=token).first()
        print(f"Received user: {user}")  # Debug log

        if not user:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        data = request.data.copy()
        data['user'] = user.id  # Associate the data with the user

        serializer = SensorDataSerializer(data=data)

        if serializer.is_valid():
            serializer.save()  # Save the data with the user association
            return Response({'message': 'Data saved successfully'}, status=status.HTTP_201_CREATED)
        else:
            print(f"Serializer errors: {serializer.errors}")  # Print any validation errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API view to get the latest sensor data for each node
class LatestSensorDataView(APIView):
    def get(self, request):
        token = request.GET.get('token')  # Get token from the request
        user = CustomUser.objects.filter(token=token).first()  # Find the user by token

        if not user:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        if not SensorData.objects.filter(user=user).exists():
            raise NotFound("No sensor data available for this user.")

        # Get the latest timestamp for each node
        latest_timestamps = SensorData.objects.filter(user=user)\
            .values('node')\
            .annotate(latest_timestamp=Max('timestamp'))

        # Get the full records for these latest timestamps
        latest_data = SensorData.objects.filter(
            user=user,
            timestamp__in=[item['latest_timestamp'] for item in latest_timestamps]
        )

        if not latest_data:
            raise NotFound("No sensor data available for this user.")

        serializer = SensorDataSerializer(latest_data, many=True)
        return Response(serializer.data)

# Dashboard view for rendering the frontend
@login_required
def dashboard(request):
    sensor_data = SensorData.objects.filter(user=request.user).order_by('-timestamp')[:50]
    return render(request, 'dashboard.html', {'sensor_data': sensor_data})

# Authentication views
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout as django_logout
from .models import CustomUser
from django.db import IntegrityError

# Signup view
def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password1 = request.POST.get("password1")
        password2 = request.POST.get("password2")
        token = request.POST.get("token")

        # Validation
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, "signup.html")

        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password1,
                token=token
            )
            login(request, user)
            return redirect("dashboard")
        except IntegrityError:
            messages.error(request, "Username, email, or token already exists.")
            return render(request, "signup.html")

    return render(request, "signup.html")

# Login view
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid credentials.")
            return render(request, "login.html")

    return render(request, "login.html")

# Logout view
def logout_view(request):
    django_logout(request)
    return redirect("login")