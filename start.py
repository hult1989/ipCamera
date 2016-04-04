import os
import subprocess
import time

os.popen('touch ./server.log')
os.popen('python init.py&')
subprocess.Popen('tail -f ./server.log&', shell=True)

