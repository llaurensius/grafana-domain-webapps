import urllib.request
from urllib.error import HTTPError

try:
    req = urllib.request.urlopen('http://localhost:8000/api/domains')
    print(req.read().decode())
except HTTPError as e:
    print("HTTP Error:", e.code)
    print(e.read().decode())
