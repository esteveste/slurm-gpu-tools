
##scontrol listpids | column -t 



# scontrol pidinfo
## diz se esta nalgum slurm process, e quando vai acabar
## FUCK, este nao mostra as seeds, o _valor

## da flag de erro se nao estiver, podemos ir buscar job id ai


# (base) besteves@nexus1:~/logs $ scontrol pidinfo 4079004 
# Slurm JobId=18542 ends at Fri Sep 22 08:30:48 2023
# Job remaining time is 140641 seconds
# (base) besteves@nexus1:~/logs $ scontrol pidinfo 3573943        
# Failed to locate job for requested pid

# (base) besteves@nexus1:~/logs $ scontrol pidinfo 4079004 
# Slurm JobId=18542 ends at Fri Sep 22 08:30:48 2023
# Job remaining time is 140590 seconds
# (base) besteves@nexus1:~/logs $ echo $?                  
# 0
# (base) besteves@nexus1:~/logs $ scontrol pidinfo 3573943 
# Failed to locate job for requested pid
# (base) besteves@nexus1:~/logs $ echo $?                 
# 1

## vai buscar gpu info
# $ squeue -j 18542 -o "%b"                                                  

# TRES_PER_NODE
# gres:shard:10



## outra hipotese xml
## nvidia-smi -q -x | grep pid

## get compute pids separados por /n
# nvidia-smi --query-compute-apps=pid --format=csv,noheader




## listpids <job_id<.step>> 


# In [18]: my_dict['nvidia_smi_log']['gpu'][0]['processes']['process_info'][0]
# Out[18]: 
# {'gpu_instance_id': 'N/A',
#  'compute_instance_id': 'N/A',
#  'pid': '643',
#  'type': 'G',
#  'process_name': '/usr/lib/Xorg',
#  'used_memory': '12 MiB'}


#  {'gpu_instance_id': 'N/A',
#   'compute_instance_id': 'N/A',
#   'pid': '4079004',
#   'type': 'C',
#   'process_name': 'python',
#   'used_memory': '17462 MiB'}

# pacman -S python-xmltodict

## FIXME this works poorly, since we cannot distinguish seeds.....
## thus we will only analyze for single gpu processes (the user could create multiple processes and screw this up...)

# cp ../users/configs/check_slurm_gpu.py .
# sudo crontab -e
# @reboot python /home/gaipsadmin/check_slurm_gpu.py &



import xmltodict
import time
import datetime
import subprocess
import os


def get_shard_jobid(jobid):
    return int(subprocess.getoutput(f'squeue -j {jobid} -o "%b" | grep shard | cut -d ":" -f 3').split("\n")[0])

def is_pid_in_slurm(pid):
    try:
        jobid=int(subprocess.getoutput(f'scontrol pidinfo {pid} | grep JobId | cut -d " " -f 2 | cut -d "=" -f 2'))
        return True, jobid
    except:
        return False, None


def check_slurm_gpu_processes():

    nvidia_smi_out = subprocess.getoutput("nvidia-smi -q -x")

    my_dict = xmltodict.parse(nvidia_smi_out)

    #get gpus, list 2
    gpus = my_dict['nvidia_smi_log']['gpu']

    # jobid_total_cuda_memory_used = {}

    for gpu in gpus:
        processes = gpu['processes']['process_info']

        for process in processes:
            if process['type'] == 'C':
                # only compute processes

                pid = process['pid']
                used_memory = int(process['used_memory'].split(" ")[0])

                print(process['pid'], process['used_memory'])

                in_slurm, jobid = is_pid_in_slurm(pid)
                if in_slurm:
                    print(f"Process {pid} is in slurm job {jobid}")
                    cuda_mem_requested = get_shard_jobid(jobid)
                    print(f"Is requesting {cuda_mem_requested} GB of cuda memory")

                    # FIXME here
                    # if jobid not in jobid_total_cuda_memory_used:
                    #     jobid_total_cuda_memory_used[jobid] = used_memory
                    # else:
                    #     jobid_total_cuda_memory_used[jobid] += used_memory


                    if used_memory > cuda_mem_requested*1000:
                        print(f"Process {pid} is using more than {cuda_mem_requested*1000} MB of cuda memory (using {used_memory} MB) - Killing")
                        os.system(f"scontrol notify {jobid} 'Your job is using more than {cuda_mem_requested*1000} MB of cuda memory (using {used_memory} MB). Thus Killed'")
                        os.system(f"scancel {jobid}")
                        
                else:
                    print(f"Process {pid} is not in slurm - Killing")
                    os.system(f"kill {pid}")

                print("------------------")



if __name__ == "__main__":
    # check every 5 minutes
    while True:
        print(f"Time: {datetime.datetime.now().strftime('%H:%M:%S')}")
        check_slurm_gpu_processes()
        # time.sleep(5*60)
        time.sleep(5)