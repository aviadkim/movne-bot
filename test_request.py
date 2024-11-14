import requests
import json

headers = {
    'Content-Type': 'application/json',
    'X-API-Key': 'your_api_key_here'
}

data = {
    'message': 'מה מובנה עושה'
}

response = requests.post('http://localhost:8080/api/chat', 
                        headers=headers,
                        json=data)

print('Status Code:', response.status_code)
print('Response:', response.text)
