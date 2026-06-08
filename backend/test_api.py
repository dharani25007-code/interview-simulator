import httpx

BASE_URL = "http://127.0.0.1:5000/api"

print("1. Registering/Logging in...")
res = httpx.post(f"{BASE_URL}/auth/login", json={
    "email": "robinsona25@karunya.edu.in",
    "password": "password" # Wait, I don't know the exact password the user entered. Let me just create a new user.
})

if res.status_code == 401:
    res = httpx.post(f"{BASE_URL}/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123"
    })

print(res.status_code, res.json())
token = res.json().get("token")

print("2. Getting Dashboard...")
res2 = httpx.get(f"{BASE_URL}/dashboard", headers={"Authorization": f"Bearer {token}"})
print(res2.status_code, res2.json())

print("3. Starting interview...")
res3 = httpx.post(f"{BASE_URL}/interviews/start", headers={"Authorization": f"Bearer {token}"}, json={
    "role": "Software Engineer",
    "level": "mid",
    "category": "mixed"
})
print(res3.status_code, res3.json())
