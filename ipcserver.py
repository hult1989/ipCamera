from twisted.web.resource import Resource
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from IpcPacket import *

BUF_SIZE = 5 * 1024 * 1024


class Session:
    def __init__(self):
        self.cameraTransport = None
        self.appTransports = list()
        self.pendingDefer = list()
        self.buf = bytearray(BUF_SIZE)
    
    def addAppTransport(self, transport):
        self.appTransports.append(transport)

    def addDefer(self, d):
        self.pendingDefer.append(d)



class IpcServer(Protocol):
    def __init__(self, session):
        #self.sessionList = sessionList
        self.session = session
        self.name = ''

    def connectionLost(self, reason):
        log.msg('connection Lost with: ' + str(self.session.cameraTransport))
        log.msg('reason is: ' + str(reason))
   
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))
        self.session.cameraTransport = self.transport
        log.msg('ONLNE CAMERA CONNECTIONS: ' + str(self.session.cameraTransport))
        '''
        log.msg('TRANSPORT OBJECT: ' + str(vars(self.transport)))
        log.msg('CLIENT: ' + str(self.transport.client))
        log.msg('SOCKET: ' + str(self.transport.socket))
        '''

    def dataReceived(self, data):
        log.msg('Camera ' + str(self.transport.getPeer()) + ' send message, len: ' + str(len(data)))
        for app in self.session.appTransports:
                app.write(data)
        self.session.buf += data
        packet, self.session.buf = getOnePacketFromBuf(self.session.buf)
        while packet:
            if packet.action == '\x02': 
                if packet.cmd == '\x01': 
                    with open('./namelist.log', 'a') as f:
                        self.name = packet.payload[:packet.payload.find('\x00')]
                        log.msg('log filename: ' + self.name) 
                        f.write(self.name)
                if packet.cmd == '\x02':
                    with open(self.name, 'a') as f:
                        f.write(packe.payload)
                    log.msg('cache file: %s, length: %d'  %(self.name, packet.payloadSize))
            packet, self.session.buf = getOnePacketFromBuf(self.session.buf)




class AppProxyFactory(Factory):
    def __init__(self, session):
        self.session = session
        
    def buildProtocol(self, addr):
        return AppProxy(self.session)


class AppProxy(Protocol):
    def __init__(self, session):
        #self.sessionList = sessionList
        self.session = session
        self.buf = ''

    def connectionLost(self, reason):
        log.msg('connection Lost with: ' + str(self.session.appTransports[-1]))
        log.msg('reason: ', str(reason))
        sesf.session.appTransports.pop()
        for app in self.session.appTransports:
            log.msg('connected app: ' + str(app))
   
    def connectionMade(self):
        self.session.appTransports.append(self.transport)
        for app in self.session.appTransports:
            log.msg('connected app: ' + str(app))

    def dataReceived(self, data):
        print 'msg from app, len: ', len(data)
        self.session.cameraTransport.write(data)
        self.buf += data
        packet, self.buf = getOnePacketFromBuf(self.buf)
        while packet:
            if packet.action == '\x01' and (packet.cmd == '\x01' or packet.cmd == '\x02'):
                with open('./AppPacketRequest.log', 'a') as f:
                    f.write(str(packet))
            packet, self.buf = getOnePacketFromBuf(self.buf)


class IpcServerFactory(Factory):
    def __init__(self, session):
        self.protocol = IpcServer(session)

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
SESSION = Session()
ipcServerFactory = IpcServerFactory(SESSION)
appProxyFactory = AppProxyFactory(SESSION)
