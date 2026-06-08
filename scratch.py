import urllib.request
import urllib.error
import json
import time

def test():
    print("Registering user...")
    try:
        req = urllib.request.Request("http://127.0.0.1:5000/api/auth/register",
                                      data=json.dumps({
                                          "name": "test", "email": f"test{time.time()}@test.com", "password": "password123"
                                      }).encode(),
                                      headers={"Content-Type": "application/json"})
        
        try:
            with urllib.request.urlopen(req) as f:
                r_json = json.loads(f.read().decode())
        except urllib.error.HTTPError as e:
            print("Register failed:", e.read().decode())
            return
            
        token = r_json.get("token")
        if not token:
            print("No token in response:", r_json)
            return
        
        print("Starting interview with token...")
        req2 = urllib.request.Request("http://127.0.0.1:5000/api/interviews/start",
                                       data=json.dumps({
                                           "role": "Software Engineer",
                                           "level": "mid",
                                           "category": "mixed"
                                       }).encode(),
                                       headers={
                                           "Content-Type": "application/json",
                                           "Authorization": f"Bearer {token}"
                                       })
        try:
            with urllib.request.urlopen(req2) as f2:
                print("Status code:", f2.getcode())
                print("Response JSON:", json.dumps(json.loads(f2.read().decode()), indent=2))
        except urllib.error.HTTPError as e:
            print("Error status code:", e.code)
            body = e.read().decode()
            try:
                print("Error JSON:", json.dumps(json.loads(body), indent=2))
            except:
                print("Error Text:", body[:500])

    except Exception as e:
        print("Exception:", str(e))

test()
