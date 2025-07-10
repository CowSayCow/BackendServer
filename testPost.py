import requests
from datetime import datetime

url = "http://localhost:8000/api/people_count"

data = {
    "camera_id": "cam01",
    "timestamp": datetime.now().isoformat(),
    "count": 45
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())