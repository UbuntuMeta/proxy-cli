import os
import subprocess
import argparse
import platform

# Define the service name
SERVICE = 'Wi-Fi'

def run(cmd, shell=True, check=True):
    subprocess.run(cmd, shell=shell, check=check)


parser = argparse.ArgumentParser()
parser.add_argument("--ip")
parser.add_argument("--port")
parser.add_argument("--off", action="store_true")
args = parser.parse_args()

if args.off:
    run(f'networksetup -setwebproxystate "{SERVICE}" off')
    run(f'networksetup -setsecurewebproxystate "{SERVICE}" off')
    # Get the os system
    system = platform.system()
    # clear the proxy for terminal
    file = os.path.expanduser("~/.zshrc")
    pattern = r"/^export[[:space:]]+(http_proxy|https_proxy|HTTP_PROXY|HTTPS_PROXY)=/d"
    if system == "Darwin":
        print("current system is macos")
        cmd = ["sed", "-i", ".bak", "-E", pattern, file]
    else:
       print(f'current system is {system}') 
       cmd = ["sed", "-i", ".bak", "-E", pattern, file]
    run(cmd, False)
    print('remove proxy successfully')
else:
    run(f'networksetup -setwebproxy "{SERVICE}" {args.ip} {args.port}')
    run(f'networksetup -setsecurewebproxy "{SERVICE}" {args.ip} {args.port}')
    run(f'networksetup -setwebproxystate "{SERVICE}" on')
    run(f'networksetup -setsecurewebproxystate "{SERVICE}" on')
    # set proxy for terminials
    run(f'echo export http_proxy=http://{args.ip}:{args.port} >> ~/.zshrc')
    run(f'echo export https_proxy=http://{args.ip}:{args.port} >> ~/.zshrc')
    print("proxy is set!")

