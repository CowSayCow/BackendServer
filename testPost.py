import requests
from datetime import datetime

url = "http://localhost:8000/api/people_count"

data = {
    "camera_id": "cam02",
    "timestamp": datetime.now().isoformat(),
    "count": 20
}

response = requests.post(url, json=data)
print(response.status_code)
print(response.json())