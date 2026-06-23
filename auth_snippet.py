import os, sys, subprocess, requests, json

API_KEY = '$2a$10$FbcN.4zlHG5ixhcgD7puI.tYJEFquC3eJ5nu2W5Ry.7dwtIxujfKO'
BIN_ID = '6a32dc52f5f4af5e29036ddd'

def get_hwid():
    try:
        hwid = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
        return hwid
    except:
        return 'UNKNOWN_HWID'

def authenticate():
    print('=========================================')
    print('     DGowdru Description Writer Pro      ')
    print('=========================================')
    key = input('Enter your License Key: ').strip()
    
    hwid = get_hwid()
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    headers = {'X-Master-Key': API_KEY.replace('\\','')}
    
    print('Verifying License Key...')
    try:
        req = requests.get(url, headers=headers)
        if req.status_code != 200:
            print(f'[ERROR] Licensing server rejected connection (Status {req.status_code}).')
            print(f'Server message: {req.text}')
            input('Press Enter to exit...')
            sys.exit(1)
        data = req.json().get('record', {})
    except Exception as e:
        print(f'[ERROR] Could not connect to licensing server: {e}')
        input('Press Enter to exit...')
        sys.exit(1)
    
    if key not in data:
        print('[ERROR] Invalid License Key!')
        input('Press Enter to exit...')
        sys.exit(1)
    
    record = data[key]
    if record.get('type') == 'universal':
        used_hwids = record.get('used_hwids', [])
        if hwid in used_hwids:
            print('[ERROR] You have already used your Free Trial on this computer!')
            print('Please purchase a full license key to continue.')
            input('Press Enter to exit...')
            sys.exit(1)
        else:
            print('Universal Free Trial Key accepted! Granting 1-time access...')
            used_hwids.append(hwid)
            data[key]['used_hwids'] = used_hwids
            requests.put(url, json=data, headers=headers)
    elif record.get('type') == 'single_use':
        print('1-Use Key Detected. Authorizing and Burning Key...')
        del data[key]
        requests.put(url, json=data, headers=headers)
        print('Key Burned Successfully! You have 1-time access.')
    else:
        if record.get('hwid') is None:
            print('First time use detected. Binding Permanent License Key to this Computer...')
            data[key]['hwid'] = hwid
            requests.put(url, json=data, headers=headers)
            print('Successfully Activated! Thank you for purchasing.')
        elif record.get('hwid') != hwid:
            print('[ERROR] This License Key is already registered to a different computer.')
            print('Sharing is strictly prohibited.')
            input('Press Enter to exit...')
            sys.exit(1)
        else:
            print('License Verified! Welcome back.')
    print('=========================================')

authenticate()
