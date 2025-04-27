import requests
import random
import time

token="4A:7B:9C:D2:E5:F8"
URL = "http://127.0.0.1:8000/api/sensor-data/"  # Replace with your actual Django API URL
# Simulated forest area near Chitwan National Park in Nepal
LATITUDE = 27.5700   # Approximate latitude for Chitwan
LONGITUDE = 84.5000  # Approximate longitude for Chitwan

def generate_sensor_data():
    return {
        "token":token,
        "node": round(random.uniform(1,5)),
        "temperature": round(random.uniform(45, 60), 2),
        "smoke": round(random.uniform(0.7, 1.2), 2),
        "flame": random.choice([0, 0, 0, 1]),  # mostly 0, sometimes 1
        "humidity": random.randint(10, 20),
        "latitude": LATITUDE + random.uniform(-0.02, 0.02),  # Adding slight randomness
        "longitude": LONGITUDE + random.uniform(-0.02, 0.02)  # Adding slight randomness
    }

while True:
    data = generate_sensor_data()
    try:
        response = requests.post(URL, json=data)
        print(f"Sent: {data} | Status: {response.status_code}")
    except Exception as e:
        print("Error sending data:", e)
    time.sleep(2)  # Send data every 2 seconds

