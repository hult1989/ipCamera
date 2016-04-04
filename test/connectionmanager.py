import time


class ConnectionManager(object):
    TASK_INTERVAL = 60
    IDLE_COUNT = 5

    def __init__(self):
        self.connectedDevices = {}
        self.validConnections = {}
        self.historicalNum = 0

    def newDeviceConnected(self, port, deviceID=None):
        self.removeDevice(deviceID)
        self.validConnections[port] = DeviceConnection(port, deviceID)
        if deviceID:
            self.connectedDevices[deviceID] = self.validConnections[port]
        self.historicalNum += 1

    def removePort(self, port):
        if port in self.validConnections:
            connection = self.validConnections[port]
            connection.disconnect()
            if connection.deviceID in self.connectedDevices:
                del self.connectedDevices[connection.deviceID]
            del self.validConnections[port]

    def removeDevice(self, deviceID):
        if deviceID in self.connectedDevices:
            connection = self.connectedDevices[deviceID]
            connection.disconnect()
            if connection.port in self.validConnections:
                del self.validConnections[connection.port]
            del self.connectedDevices[deviceID]

    def closeIdleConnection(self):
        curTime = time.time()
        for port, connection in self.validConnections.items():
            if curTime - connection.lastDataTime > self.IDLE_COUNT * self.TASK_INTERVAL:
                if not connection.busy:
                    self.removePort(port)

    def updateDeviceID(self, deviceID, port):
        connection = self.validConnections.get(port)
        if connection:
            if connection.deviceID and connection.deviceID != deviceID:
                raise Exception('different deviceID sent from same port')
            self.validConnections[port].deviceID = deviceID
        else:
            self.newDeviceConnected(port, deviceID)


class DeviceConnection(object):
    def __init__(self, transport, deviceID=None):
        self.initTime = time.time()
        self.lastDataTime = self.initTime
        self.port = transport
        self.deviceID = deviceID
        self.totalSend = 0
        self.totalRecv = 0
        self.busy = False

    def __str__(self):
        return vars(self)

    def sendData(self, data):
        self.port.write(data)
        self.totalSend += len(data)
        self.lastDataTime = time.time()

    def recvData(self, data):
        self.totalRecv += len(data)
        self.lastDataTime = time.time()

    def disconnect(self, force=False):
        try:
            if force:
                self.port.abortConnection()
            else:
                self.port.loseConnection()
        except Exception as e:
            print e

