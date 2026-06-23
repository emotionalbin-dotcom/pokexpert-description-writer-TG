import requests
API_KEY = '$2a$10$GM9kw05JzUk52CLfbar5ruhn6xImYYbQZCWuG0zXORYP3JHhFEACG'
url = 'https://api.jsonbin.io/v3/b'
headers = {
    'X-Master-Key': API_KEY,
    'Content-Type': 'application/json',
    'X-Bin-Private': 'true',
    'X-Bin-Name': 'DGowdru_DB'
}
data = {'DGowdru-UNIVERSAL': {'used_hwids': [], 'type': 'universal'}}

req = requests.post(url, json=data, headers=headers)
print(req.status_code)
print(req.text)
