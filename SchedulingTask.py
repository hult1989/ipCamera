from twisted.internet import task
from twisted.internet import reactor
from IpcPacket import *

class SchedulingTask(object):
    def __init__(self):
        self.appPortList = list()
        self.cameraPortList = list()

    def addAppPort(self, appPort):
        self.appPortList.append(appPort)

    def addCameraPort(self, cameraPort):
        self.cameraPortList.append(cameraPort)

    def syncRequest(self):
        for port in self.cameraPortList:
            port.write(str(GetListCmdPacket(addHeader('', 0))))
        print '==== sync request sent ====='
