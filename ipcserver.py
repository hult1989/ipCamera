from twisted.web.resource import Resource
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
#from ipcserver import IpcServerFactory

BUF_SIZE = 5 * 1024 * 1024


class Session:
    def __init__(self, cameraTransport):
        self.cameraTransport = cameraTransport
        self.appTransports = list()
        self.pendingDefer = list()
        self.buf = bytearray(BUF_SIZE)
    
    def addAppTransport(self, transport):
        self.appTransports.append(transport)

    def addDefer(self, d):
        self.pendingDefer.append(d)



class IpcServer(Protocol):
    def __init__(self, sessionList):
        self.sessionList = sessionList

    def connectionLost(self):
        log.msg('connection Lost with: ' + self.sessionList[0].cameraTransport)
   
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))
        self.sessionList.append(Session(self.transport))
        log.msg('ONLNE CAMERA CONNECTIONS: ' + str(self.sessionList))
        log.msg('SESSIONS:\n')
        for session in self.sessionList:
            log.msg(str(session))

    def dataReceived(self, data):
        log.msg('Camera ' + str(self.transport.getPeer()) + ' send message, len: ' + str(len(data)))
        for session in self.sessionList:
            for app in session.appTransports:
                app.write(data)




class AppProxyFactory(Factory):
    def __init__(self, sessionList):
        self.sessionList = sessionList
        
    def buildProtocol(self, addr):
        return AppProxy(self.sessionList)


class AppProxy(Protocol):
    def __init__(self, sessionList):
        self.sessionList = sessionList

    def connectionLost(self):
        log.msg('connection Lost with: ' + self.sessionList[0].appTransports[-1])
   
    def connectionMade(self):
        for session in self.sessionList:
            session.appTransports.append(self.transport)
        log.msg('SESSIONS:\n')
        for session in self.sessionList:
            log.msg(str(session))
        log.msg('ONLNE APP CONNECTIONS: ' + str(self.sessionList[0].appTransports[-1]))

    def dataReceived(self, data):
        print 'msg from app: ', data
        self.sessionList[0].cameraTransport.write(data)


class IpcServerFactory(Factory):
    def __init__(self, sessionList):
        self.protocol = IpcServer(sessionList)

    def buildProtocol(self, addr):
        return self.protocol
'''

class MainPage(Resource):
    isLeaf = True

    def __init__(self, protocol):
        self.ipcProtocol = protocol

    def getMsgFromCamera(self, transport, message, request):
        transport.write(message)
        d = Deferred()
        self.ipcProtocol.devicePair.request = request
        self.ipcProtocol.devicePair.d = d
        log.msg(str(vars(self.ipcProtocol.devicePair)))
        return d


    def render_POST(self, request):

        @inlineCallbacks
        def responseAPP(transport, message, request):
            appRes = yield self.getMsgFromCamera(transport, message, request)
            print 'appres from yield is: ', str(appRes), appRes.__class__
            request.write(appRes)
            request.finish()
            returnValue(str(appRes))

        appPayload = str(request.content.read())
        log.msg('write to connection %s' %(str(self.ipcProtocol.devicePair),))
        appRes = responseAPP(self.ipcProtocol.devicePair.transport, appPayload, request)
        print 'RESULT FROM RETURNVALUE', appRes, appRes.__class__
        return NOT_DONE_YET

        
'''
SESSIONLIST = list()
ipcServerFactory = IpcServerFactory(SESSIONLIST)
appProxyFactory = AppProxyFactory(SESSIONLIST)
