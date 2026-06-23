import os
import sys

with open('parse_final_locked.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace authenticate() call with authenticate() + start_interceptor()
interceptor_code = '''
def start_interceptor():
    import atexit
    if hasattr(sys, '_MEIPASS'):
        interceptor_path = os.path.join(sys._MEIPASS, 'Eldorado_Interceptor.exe')
    else:
        interceptor_path = 'dist/Eldorado_Interceptor.exe'
    
    print('Starting Eldorado Interceptor in the background...')
    try:
        CREATE_NO_WINDOW = 0x08000000
        process = subprocess.Popen([interceptor_path], creationflags=CREATE_NO_WINDOW)
        atexit.register(lambda: process.kill())
        print('Interceptor started successfully! Listening for data.')
        return process
    except Exception as e:
        print(f'[ERROR] Could not start the Interceptor: {e}')
        input('Press Enter to exit...')
        sys.exit(1)

authenticate()
start_interceptor()
'''

code = code.replace('authenticate()\n', interceptor_code)

with open('parse_final_locked.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched successfully!')
