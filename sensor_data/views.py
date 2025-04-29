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
from datetime import datetime, timedelta
import pytz
import uuid
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
            return Response([], status=status.HTTP_200_OK)  # Return empty array instead of raising NotFound

        # Define a time window for fresh data (e.g., last 5 seconds)
        time_threshold = datetime.now(pytz.UTC) - timedelta(seconds=5)

        # Get the latest timestamp for each node within the time window
        latest_timestamps = SensorData.objects.filter(
            user=user,
            timestamp__gte=time_threshold
        ).values('node').annotate(latest_timestamp=Max('timestamp'))

        # Get the full records for these latest timestamps
        latest_data = SensorData.objects.filter(
            user=user,
            timestamp__in=[item['latest_timestamp'] for item in latest_timestamps]
        )

        if not latest_data.exists():
            return Response([], status=status.HTTP_200_OK)  # Return empty array for no fresh data

        serializer = SensorDataSerializer(latest_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
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

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
@login_required
def user_settings(request):
    user = request.user  # This is an instance of CustomUser

    if request.method == 'POST':
        # Get form data
        email = request.POST.get('email')
        token = request.POST.get('token')

        # Validate and update email
        if email:
            try:
                validate_email(email)
                if CustomUser.objects.filter(email=email).exclude(id=user.id).exists():
                    messages.error(request, 'This email is already in use.')
                    return redirect('user_settings')
                user.email = email
            except ValidationError:
                messages.error(request, 'Invalid email address.')
                return redirect('user_settings')

        # Validate and update token
        if token:
            if len(token) != 17:
                messages.error(request, 'Token must be exactly 17 characters long.')
                return redirect('user_settings')
            if CustomUser.objects.filter(token=token).exclude(id=user.id).exists():
                messages.error(request, 'This token is already in use.')
                return redirect('user_settings')
            user.token = token

        # Save changes if validation passes
        user.save()
        messages.success(request, 'Profile updated successfully.')

        return redirect('user_settings')

    context = {
        'user': user,
    }
    return render(request, 'user.html', context)
from django.utils import timezone
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
@login_required
def sensor_data_visualization(request):
    logger.info("Starting sensor_data_visualization view")
    
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)

    user = request.user
    # Fetch the most recent 100 records for initial display
    sensor_data = SensorData.objects.filter(
        user=user,
        timestamp__range=(start_date, end_date)
    ).select_related('user').order_by('-timestamp')[:100]  # Order by most recent

    # If no data in the last 7 days, fetch the most recent 100 records overall
    if not sensor_data.exists():
        logger.info("No data found for last 7 days, fetching recent data")
        sensor_data = SensorData.objects.filter(user=user).select_related('user').order_by('-timestamp')[:100]
    
    # Get distinct nodes from the entire dataset
    nodes = SensorData.objects.filter(user=user).values_list('node', flat=True).distinct()
    logger.info(f"Found {len(nodes)} distinct nodes")

    # Prepare chart data for the most recent 100 records per node
    chart_data = {}
    for node in nodes:
        node_data = SensorData.objects.filter(
            user=user,
            node=node,
            timestamp__range=(start_date, end_date)
        ).select_related('user').order_by('-timestamp')[:100]  # Limit to 100 per node

        if not node_data.exists() and not sensor_data.exists():
            node_data = SensorData.objects.filter(user=user, node=node).select_related('user').order_by('-timestamp')[:100]
        
        if node_data.exists():
            chart_data[str(node)] = {
                'timestamps': [data.timestamp.strftime('%Y-%m-%d %H:%M:%S') for data in node_data],
                'temperatures': [data.temperature for data in node_data],
                'smoke': [data.smoke for data in node_data],
                'humidity': [data.humidity for data in node_data],
                'flame': [1 if data.flame else 0 for data in node_data],
            }
            logger.info(f"Chart data for node {node}: {chart_data[str(node)]}")
    
    logger.info(f"Prepared chart data for {len(chart_data)} nodes")

    context = {
        'sensor_data': sensor_data,
        'chart_data': chart_data,
        'nodes': list(chart_data.keys()),
    }
    logger.info("Rendering sensor_data_visualization.html")
    return render(request, 'sensor_data_visualization.html', context)