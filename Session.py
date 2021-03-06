from util.BandwidthTester import BandwidthTester

class FileStatus(object):
    PENDING = 0
    NXIST = -1
    EXIST = 1
    ERROR = -2


class Session(object):
    RQSTLIST = 1
    RQSTFILE = 2
    RQSTVIDEO = 3

    class Conversion(object):
        def __init__(self, appPort, appId, cameraPort, state):
            self.activeAppPort = appPort
            self.appId = appId
            self.state = state
            self.unfinished = None
            self.time = None
            self.filename = None

        def getActiveApp(self):
            return self.activeAppPort

    def __init__(self, cameraId=None, cameraPort=None):
        self.cameraId = cameraId
        self.cameraPort = cameraPort 
        self.appPorts = dict()
        self.appLastPushTime = dict()
        self.sessBuf = None
        self.conversion = None
        self.streamingClients = set()
        self.bandwidthTester = BandwidthTester()
        self.fileList = dict()
        self.unfinished = None

    def getPendingName(self):
        for name in self.fileList:
            if self.fileList[name] == FileStatus.PENDING:
                return name
        return None

    def getCachePath(self):
        return '/'.join(('./cached', str(hash(self.cameraId))))


    def addAppTransport(self, appId, appTransport):
        self.appPorts[appId] = appTransport

    def getAppTransport(self, appId):
        try:
            return self.appPorts[appId]
        except:
            return None

    def getAppIdByPort(self, appPort):
        for appId in self.appPorts:
            if self.appPorts[appId] == appPort:
                return str(appId)
        return None


    def getAllAppPorts(self):
        for appId in self.appPorts:
            yield self.appPorts[appId]

    def getActiveApp(self):
        if self.conversion:
            return self.conversion.getActiveApp()
        else:
            return None

    def removeStreamingClient(self, appId):
        self.streamingClients.remove(appId)

    def addStreamingClient(self, appId):
        self.streamingClients.add(appId)

    def getStreamingClient(self):
        return list(self.streamingClients)

class SessionList(object):
    def __init__(self):
        self.sessions = dict()

    def getAllSession(self):
        for cameraId in self.sessions:
            yield self.sessions[cameraId]

    def addSession(self, cameraId, session):
        self.sessions[cameraId] = session

    def getSessionByCamId(self, cameraId):
        if not self.sessions.has_key(cameraId):
            return None
        return self.sessions[cameraId]

    def getSessionsByAppId(self, appId):
        result = list()
        for session in self.sessions.values():
            if session.appPorts.has_key(appId):
                result.append(session)
        return result if len(result) != 0 else None

    def getSessionByAppPort(self, appPort):
        for session in self.sessions.values():
            if appPort in session.appPorts.values():
                return session
        return None

    def getSessionByCamPort(self, cameraPort):
        for session in self.sessions.values():
            if session.cameraPort == cameraPort:
                return session
        return None

    def isEmpty(self):
        return len(self.sessions) == 0

    def __len__(self):
        return len(self.sessions)


if __name__ == '__main__':
    sessiona = Session('alice', '192.168.1.1:1080')
    sessiona.addAppTransport('2046', '219.2223.192.138:8080')
    sessiona.addAppTransport('1984', '219.223.199.48:8080')
    sessionb = Session('bob', '192.168.1.1:1080')
    sessionb.addAppTransport('2046', '219.2223.192.138:8080')
    sl = SessionList()
    sl.addSession(sessiona.cameraId, sessiona)
    sl.addSession(sessionb.cameraId, sessionb)

    print id(sl.getSessionByCamId('alice'))
    for session in sl.getSessionsByAppId('2046'):
        print id(session)


