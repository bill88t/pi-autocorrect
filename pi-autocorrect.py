#!/usr/bin/env python3

from sys import argv
from os import system, getuid
from time import time, sleep
from datetime import datetime
import json
import subprocess
from psutil import boot_time

def getuptime():
    return int(time() - boot_time())

def ping(ip): # returns true on failure
    return bool(system(f"ping -c 1 {ip}"))

def roottest(): # returns true when run as the user
    return True if getuid()!=0 else False

def restart(): # reboots the host
    system("shutdown -r now")
    
def log_restart(fnam): # logs time we rebooted
    with open(fnam, "a") as filee:
        filee.write(
            f"Rebooted @ {datetime.now().day}-{datetime.now().month}-{datetime.now().year} {datetime.now().hour}:{datetime.now().minute}\n"
        )

Version = "0.1"

"""
dry-run, does not perform any actions for real
ping, pings internet computers
lanping, pings local compooters
strict, any test failures result to corrective action
systemd, looks for fallen services
config, it's location
debug, is debug
"""
args = {"dry-run": False, "ping": False, "lanping": False, "strict": False, "systemd": False, "config": "None", "debug": False}
detargs = ""

look_away = False
for i in range(1, len(argv)):
    if argv[i][2:] in args:
        if isinstance(args[argv[i][2:]], str):
            look_away = True
            try:
                args[argv[i][2:]] = argv[i+1]
                detargs += f"{argv[i][2:]}={args[argv[i][2:]]} "
            except IndexError:
                print("Error: Not enough arguments")
                exit(1)
        else:
            args[argv[i][2:]] = True
            detargs += argv[i][2:] + " "
    else:
        if not look_away:
            print(f"{argv[i][2:]} not understood")
            exit(1)
del look_away

print(f"""
      Raspberry Pi Autocorrect
      Author: bill88t (Bill Sideris)
      Version: {Version}
      Options detected: \"{detargs[:-1]}\"
      """)

del detargs

# config file stuff
configg = None
if args["config"] == "None":
    print("Error: A config file is required for the program to function")
    exit(1)
try:
    with open(args["config"], "r") as cf:
        configg = json.loads(cf.read())
except OSError:
    print("Error: Could not open config file")
    exit(1)
except json.decoder.JSONDecodeError:
    print("Error: Could not parse config file")
    exit(1)

# check if system has just restarted (<3 minutes uptime)
if getuptime() < 180:
    print("The system has just rebooted, leaving it to cool off")
    exit(0)

# check if rebooted due to ourselves
clear_mode = False
if configg["status"] != 0:
    print("""
          The system has been rebooted by autocorrect.
          Not applying further corrective actions till the status is cleared.
          """)
    clear_mode = True
    

# test if we have root priviledges
if roottest():
    if args["dry-run"]:
        print("Warning, this script is meant to be run as root\n")
    else:
        print("Error: This script has to be run as root")
        exit(1)

need_restart = False
internet_down = False
lan_down = False
method_specified = False

# test if we can ping internet computers
if args["ping"]:
    method_specified = True
    print("Attempting a ping test: ")
    anygood = False
    for i in configg["int_pings"]:
        if not ping(i):
            print("Ping success!")
            anygood = True
        else:
            print("Ping failed!")
    if not anygood and len(configg["int_pings"]) > 0:
        internet_down = True
    del anygood
        
# test if we can ping local computers
if args["lanping"]:
    print("Attempting a lan ping test:")
    anygood = False
    for i in configg["lan_pings"]:
        if not ping(i):
            anygood = True
    if not anygood and len(configg["lan_pings"]) > 0:
        lan_down = True
    del anygood
    
if args["systemd"]:
    print("Not implemented")

# debug prints
if args["debug"]:
    print(f"""
           need_restart: {str(need_restart)}
           internet_down: {str(internet_down)}
           lan_down: {str(lan_down)}
           method_specified: {str(method_specified)}
           """)

# determine corrective action
if (internet_down and lan_down) or ((internet_down or lan_down) and args["strict"]):
    need_restart = True
else:
    configg["status"] = 0

del internet_down, lan_down, method_specified

# am I gonna really do it?
do_it = False
drr = args["dry-run"]
del drr
if need_restart and (not args["dry-run"]) and (not clear_mode):
    do_it = True

# write new config
configg["lasttime"] = getuptime()
if do_it:
    configg["status"] = 1
with open(args["config"], "w") as cf:
    cf.write(json.dumps(configg))

del configg

# all or nothing
if do_it:
    log_restart(configg["logfile"])
    print("ALERT: APPLYING CORRECTIVE ACTION")
    restart()
    # we need no exit
else:
    exit(0)
