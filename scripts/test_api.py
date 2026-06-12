import urllib.request, json
try:
    data = json.loads(urllib.request.urlopen('http://localhost:8000/api/domains/').read())
    for d in data:
        if 'corona' in d['url'] or 'bpsdmd' in d['url']:
            print(f"{d['url']} -> {d['error_info']}")
except Exception as e:
    print(e)
