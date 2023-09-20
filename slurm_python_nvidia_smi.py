# watch -n 2 cat  /home/users/public/nvidia_smi.nexus1

# cp ../users/configs/share_nvidia_smi.py .
# sudo crontab -e
# @reboot python /home/gaipsadmin/share_nvidia_smi.py  & 

import time
import os
import subprocess


if __name__ == "__main__":
    server_name = subprocess.getoutput("hostname")

    while True:
        file = f"nvidia_smi.{server_name}"
        os.system(f"rm -f {file} && nvidia-smi > {file}")
        time.sleep(2)