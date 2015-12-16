# -*- coding:utf-8 -*-
from twisted.web.resource import Resource
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
import time
from IpcPacket import *
from Session import *





class IpcServer(Protocol):
    def __init__(self, sessionList):
        self.sessionList = sessionList
        self.timestamp = 0
        self.totalSize = 0
        self.serverBuf = dict()

    def cameraConnected(self, cameraId, cameraPort):
        self.sessionList.addSession(cameraId, Session(cameraId, cameraPort))
        log.msg('==== camera %s connected=============' %(cameraId))
        for session in self.sessionList.getAllSession():
            log.msg('ACTIVE SESSION' + str(vars(session)))


    def connectionLost(self, reason):
        #log.msg('connection Lost with: ' + str(self.session.cameraTransport))
        log.msg('reason is: ' + str(reason))
   
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))
        '''
        log.msg('TRANSPORT OBJECT: ' + str(vars(self.transport)))
        log.msg('CLIENT: ' + str(self.transport.client))
        log.msg('SOCKET: ' + str(self.transport.socket))
        '''
    def calcRate(self, data):
        now = time.time()
        if self.timestamp == 0 and self.totalSize == 0:
            self.timestamp = now
            self.totalSize = len(data)
        else:
            self.totalSize += len(data)
            if now - self.timestamp > 10:
                log.msg('CURRENT RATE: %.1f KB/s' %( self.totalSize / float(now - self.timestamp) / 1024,))
                self.timestamp = 0
                self.totalSize = 0


    def dataReceived(self, data):

        packet, buf = getOnePacketFromBuf(data)
        self.cameraConnected(packet.payload, self.transport)
        
        '''
        session = self.sessionList.getSessionByCamPort(self.transport)
        log.msg( session.cameraId + ' send message, lenth: ' + str(len(data)))
        session.getActiveApp.write(data)

        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
        while packet:
            if isinstance(packet, HelloPacket):
                self.cameraConnected(packet.payload, self.transport)
            elif packet.cmd == '\x01':  
                with open('./namelist.log', 'w') as f:
					for name in getFileListFromPayload(packet.payload):
						f.write(name + '\n')
            elif packet.cmd == '\x02':
                log.msg('WRITE TO FILE%s' %(self.session.name))
                with open(self.session.name, 'a') as f:
                    f.write(packet.payload)
                    #log.msg('cache file: %s, length: %d'  %(self.name, packet.payloadSize))
            packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
        '''



class AppProxyFactory(Factory):
    def __init__(self, sessionList):
        self.sessionList = sessionList
        
    def buildProtocol(self, addr):
        return AppProxy(self.sessionList)


class AppProxy(Protocol):
    def __init__(self, sessionList):
        #self.sessionList = sessionList
        self.sessionList = sessionList
        self.serverBuf = dict()

    def connectionLost(self, reason):
        log.msg('reason: ', str(reason))
   
    def connectionMade(self):
        if self.sessionList.isEmpty():
            self.transport.write('No camera on line')
            self.transport.loseConnection()

    def processPacket(self, packet, appPort):
        if isinstance(packet, HelloPacket):
            appId, cameraId = packet.payload.split()
            self.connectCamera(appId, cameraId, appPort)
            appPort.write(IpcPacket.CONNECTED)
        elif isinstance(packet, GetListCmdPacket):
            cameraPort = self.sessionList.getSessionByAppPort(appPort).cameraPort
            cameraPort.write(str(packet))


    def connectCamera(self, appId, cameraId, appPort):
        if not self.sessionList.getSessionByAppPort(appPort):
            self.sessionList.getSessionByCamId(cameraId).addAppTransport(appId, self.transport)
            log.msg(vars(self.sessionList.getSessionByCamId(cameraId)))
        else:
            raise Exception('App already exists in session')


    def dataReceived(self, data):
        print '======== server received data: %s =============' %(data[12:],)
        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
        if not packet:
            return 
        self.processPacket(packet, self.transport)



        '''
        
        while packet:
            print packet.payload
            if isinstance(packet, HelloPacket):
                appId, cameraId = packet.payload.split()
                if not self.sessionList.has_key(cameraId):
                    raise Exception('No camera connected')
                self.sessionList[cameraId].setAppTransport(appId, self.transport)
                log.msg('======== CmaeraId: %s, online app %s ==============' %(cameraId, str(self.sessionList[cameraId].appPorts)))
            elif packet.action == '\x01' and (packet.cmd == '\x01' or packet.cmd == '\x02'):
                with open('./AppPacketRequest.log', 'w') as f:
                    f.write(str(packet))
            elif packet.cmd == '\x02':
                self.session.name = packet.payload[:packet.payload.find('\x00')]
                log.msg('APP REQUEST FILE %s\t' %(self.session.name))
            packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
        '''


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
SESSIONLIST = SessionList()
ipcServerFactory = IpcServerFactory(SESSIONLIST)
appProxyFactory = AppProxyFactory(SESSIONLIST)
