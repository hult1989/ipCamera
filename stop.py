import os

try:
    pid1 = os.popen('ps aux | grep \[i]nit.py').readline().split()[1]
    pid2 = os.popen('ps aux | grep \[c]amera.py').readline().split()[1]
except:
    try:
        pid1 = os.popen('ps aux | grep \[i]nit.py').readline().split()[1]
    except:
        pid2 = os.popen('ps aux | grep \[c]amera.py').readline().split()[1]


try:
    os.system('kill -9 %s %s' %(pid1, pid2))
except:
    try:
        os.system('kill -9 %s' %(pid1))
    except:
        os.system('kill -9 %s' %(pid2))
finally:
    os.system('pkill tail')

