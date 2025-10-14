import requests

headers = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzYyOTU1MjkyfQ.OsCM5bejLXYcSXjtQvUuEezNhtNFCvgvbHUKJv2Gq78"
}

requisicao = requests.get("http://127.0.0.1:8000/auth/refresh", headers=headers)


print("Status code:", requisicao.status_code)
print(requisicao.json())