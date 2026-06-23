import os, sys, requests, json
API_KEY = '$2a$10$FbcN.4zlHG5ixhcgD7puI.tYJEFquC3eJ5nu2W5Ry.7dwtIxujfKO'
BIN_ID = '6a32dc52f5f4af5e29036ddd'

def generate_key(key_type='permanent'):
    import string, random
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(random.choice(chars) for _ in range(12))
    if key_type == 'permanent':
        return f'DGowdru-{suffix}'
    elif key_type == 'universal':
        return 'DGowdru-UNIVERSAL'
    else:
        return f'DG1USE-{suffix}'

def add_key_to_db(key, key_type):
    url = f'https://api.jsonbin.io/v3/b/{BIN_ID}'
    headers = {'X-Master-Key': API_KEY.replace('\\', '')}
    
    print('Fetching current database...')
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
        
    if key_type == 'universal':
        data[key] = {'used_hwids': [], 'type': key_type}
    else:
        data[key] = {'hwid': None, 'type': key_type}
    
    print(f'Adding {key} to database...')
    req = requests.put(url, json=data, headers=headers)
    if req.status_code == 200:
        print('Success!')
    else:
        print(f'Failed to add key. Status {req.status_code}')
        print(f'Server message: {req.text}')
        input('Press Enter to exit...')

def main():
    while True:
        print('=========================================')
        print('     DGowdru Key Manager Pro             ')
        print('=========================================')
        print('[1] Generate Permanent Key (Locks to 1 PC)')
        print('[2] Generate 1-Use Key (Burns on entry)')
        print('[3] Initialize Universal Trial Key (DGowdru-UNIVERSAL)')
        choice = input('Select option (1/2/3): ').strip()
        
        if choice == '1':
            key = generate_key('permanent')
            print(f'Generated Permanent Key: {key}')
            add_key_to_db(key, 'permanent')
            input('Press Enter to continue...')
        elif choice == '2':
            key = generate_key('1-use')
            print(f'Generated 1-Use Key: {key}')
            add_key_to_db(key, 'single_use')
            input('Press Enter to continue...')
        elif choice == '3':
            key = generate_key('universal')
            print(f'Initializing Universal Key: {key}')
            add_key_to_db(key, 'universal')
            input('Press Enter to continue...')
        else:
            print('Invalid choice.')
            input('Press Enter to continue...')

if __name__ == '__main__':
    main()
