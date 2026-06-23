import requests
API_KEY = '$2a$10$FbcN.4zlHG5ixhcgD7puI.tYJEFquC3eJ5nu2W5Ry.7dwtIxujfKO'
url = 'https://api.jsonbin.io/v3/b'
headers = {'X-Master-Key': API_KEY, 'Content-Type': 'application/json', 'X-Bin-Private': 'true', 'X-Bin-Name': 'DGowdru_DB'}
data = {'DGowdru-UNIVERSAL': {'used_hwids': [], 'type': 'universal'}}
req = requests.post(url, json=data, headers=headers)
print('POST create bin:', req.status_code, req.text)