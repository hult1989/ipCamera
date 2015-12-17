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
        self.serverBuf = dict()
        self.sent = None

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
    def calcRate(self, data, conversion):
        now = time.time()
        if conversion.time is None:
            conversion.time = now
            self.timestamp = now
            self.totalSize = len(data)
        else:
            self.totalSize += len(data)
            if now - self.timestamp > 10:
                log.msg('CURRENT RATE: %.1f KB/s' %( self.totalSize / float(now - self.timestamp) / 1024,))
                self.timestamp = 0
                self.totalSize = 0

    def processPacket(self, packet, cameraPort):
        if isinstance(packet, HelloPacket):
            self.cameraConnected(packet.payload, cameraPort)
        elif isinstance(packet, FileListPacket) or isinstance(packet, FilePacket):
            session = self.sessionList.getSessionByCamPort(cameraPort)
            while packet:
                session.getActiveApp().write(str(packet))
                if isinstance(packet, FileListPacket):
                    if self.cacheFileList(packet, session.conversion):
                        print '======== LIST ACCEPTED========='
                        session.conversion = None
                        self.serverBuf[str(cameraPort)] = ''
                        print '======= Conversion CLOSED ========'
                elif isinstance(packet, FilePacket):
                    if self.cacheFile(packet, session.conversion):
                        print '======== FILE ACCEPTED========='
                        session.conversion = None
                        self.serverBuf[str(cameraPort)] = ''
                        print '======= Conversion CLOSED ========'
                packet, self.serverBuf[str(cameraPort)] = getOnePacketFromBuf(self.serverBuf[str(cameraPort)])


    def cacheFileList(self, packet, conversion):
        with open('./namelist.log', 'a') as f:
            if conversion.unfinished is None:
                conversion.unfinished = packet.totalMsgSize
            conversion.unfinished -= packet.payloadSize
            print '=========MSG LEFT %d ===========' %(conversion.unfinished)
            for name in getFileListFromPayload(packet.payload):
                f.write(name + '\n')
            if conversion.unfinished == 0:
                conversion.unfinished = None
            return conversion.unfinished is None

    def cacheFile(self, packet, conversion):
        if conversion.unfinished is None:
            conversion.unfinished = packet.totalMsgSize
        conversion.unfinished -= packet.payloadSize
        with open('./saved/' + conversion.filename, 'a') as f:
            f.write(packet.payload)
        #print '=========MSG LEFT %d ===========' %(conversion.unfinished)
        if conversion.unfinished == 0:
            conversion.unfinished = None
        return conversion.unfinished is None

    def dataReceived(self, data):
        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
        if not packet:
            return 
        self.processPacket(packet, self.transport)

        
        '''

        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packet, self.serverBuf[str(self.transport)] = getOnePacketFromBuf(self.serverBuf[str(self.transport)])
            if isinstance(packet, HelloPacket):
                self.cameraConnected(packet.payload, self.transport)
            elif packet.cmd == '\x01':  
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
        elif isinstance(packet, GetListCmdPacket) or isinstance(packet, GetFileCmdPacket):
            session = self.sessionList.getSessionByAppPort(appPort)
            cameraPort = session.cameraPort
            if session.conversion is None:
                print '======= Conversion OPEN ========'
                session.conversion = Session.Conversion(appPort, cameraPort, Session.RQSTLIST)
                if isinstance(packet, GetFileCmdPacket): 
                    session.conversion.state = Session.RQSTFILE
                    session.conversion.filename = packet.payload[:packet.payload.find('\x00')]
                cameraPort.write(str(packet))
            else:
                appPort.write('Camera busy, wait a minute')



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
