# -*- coding:utf-8 -*-
from twisted.web.resource import Resource
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
import time
from util.BandwidthTester import BandwidthTester
from IpcPacket import *
from Session import *



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
        log.msg('====APP %s CONNECTED ====' %(str(self.transport.client)))
        #self.transport.loseConnection()

    def respWithCachedFile(self, appPort, filePath):
        print 'response with cached file'.center(40, '*')
        log.msg('**** cached file %s ****' %(filePath))
        with open(filePath) as f:
            filePayload = f.read()
        for packetPayload in buffer2packets(filePayload):
            packet = str(FilePacket(packetPayload))
            appPort.write(packet)
        print 'response finished'.center(40, '*')

    def respWithFileUrl(self, appPort, filePath):
        url = 'http://116.7.225.58:8082/' + filePath[9:]
        msg = str(FilePacket(addHeader(url, len(url))))
        appPort.write(msg)

    def processGetFilePacket(self, packet, appPort):
        session = self.sessionList.getSessionByAppPort(appPort)
        cameraPort = session.cameraPort
        filename = packet.payload[:packet.payload.find('\x00')]
        filePath= '/'.join((session.getCachePath(), filename))
        if os.path.exists(filePath):
            #self.respWithCachedFile(appPort, filePath)
            self.respWithFileUrl(appPort, filePath)
        '''
        elif session.conversion is None:
            print '======= FILE Conversion OPEN ========'
            appId = session.getAppIdByPort(appPort)
            session.conversion = Session.Conversion(appPort, appId, cameraPort, Session.RQSTLIST)
            session.conversion.state = Session.RQSTFILE
            session.conversion.filename = filename
            cameraPort.write(str(packet))
        else:
            appId = session.getAppIdByPort(appPort)
            if session.conversion.appId == appId:
                print '=== FRESH CONVERSION ==='
                session.conversion.appPort = appPort
                cameraPort.write(str(packet))
            else:
                errPacket = FileListErrPacket(IpcPacket(addHeader('camera busy', 11)))
                appPort.write(str(errPacket))
        '''

    def processGetListPacket(self, packet, appPort):
        session = self.sessionList.getSessionByAppPort(appPort)
        payload = ''
        for name in session.fileList:
            if session.fileList[name] == FileStatus.EXIST:
                payload += name
                payload += '\x00' * (32-len(name))
        appPort.write(str(FileListPacket(addHeader(payload, len(payload)))))


    def processPacket(self, packets, appPort):
        for packet in packets:
            if isinstance(packet, HelloPacket):
                log.msg('hello packet id %s' %(packet.payload))
                appId, cameraId = packet.payload[:7], packet.payload[7:]
                self.connectCamera(appId, cameraId, appPort)
            elif isinstance(packet, GetListCmdPacket):
                self.processGetListPacket(packet, appPort)
            elif isinstance(packet, GetFileCmdPacket):
                self.processGetFilePacket(packet, appPort)
            elif isinstance(packet, GetStreamingPacket):
                session = self.sessionList.getSessionByAppPort(appPort)
                appId = session.getAppIdByPort(appPort)
                session.addStreamingClient(appId)
                cameraPort = session.cameraPort
                cameraPort.write(str(packet))
                log.msg('==== Steaming Clients %s ====' %(str(session.getStreamingClient())))
            elif isinstance(packet, CloseStreamingPacket):
                session = self.sessionList.getSessionByAppPort(appPort)
                print '====== dropping streaming client ===='
                cameraPort = session.cameraPort
                appId = session.getAppIdByPort(appPort)
                session.removeStreamingClient(appId)
                if len(session.getStreamingClient()) == 0:
                    cameraPort.write(str(packet))





    def connectCamera(self, appId, cameraId, appPort):
        if not self.sessionList.getSessionByCamId(cameraId):
            appPort.write(str(HelloErrPacket(addHeader('no camera online', 16))))
            appPort.loseConnection()
        #elif not self.sessionList.getSessionByAppPort(appPort):
        else:
            appPort.write(str(HelloAckPacket(addHeader('', 0))))
            self.sessionList.getSessionByCamId(cameraId).addAppTransport(appId, appPort)
            log.msg(' *** %s has connected appports : *** ' %(str(list(cameraId))))
            for (appId, port) in self.sessionList.getSessionByCamId(cameraId).appPorts.items():
                log.msg(' *** port %s -- %s connected ***' %(appId, str(port.client)))
            log.msg('-----------------------------------------------------')
            log.msg('=== ONLINE SESSION: %s ===' %(vars(self.sessionList.getSessionByCamId(cameraId))))
        #else:
            #raise Exception('App already exists in session')


    def dataReceived(self, data):

        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packets, self.serverBuf[str(self.transport)] = getAllPacketFromBuf(self.serverBuf[str(self.transport)])
        if packets:
            self.processPacket(packets, self.transport)
        else:
            log.msg( '======== server received data: %s      ========' %(str(data)))
            if data.find('force') != -1:
                for session in self.sessionList.sessions.values():
                    session.cameraPort.write(str(CloseStreamingPacket(addHeader('', 0))))
                log.msg('--------- force all camera stop streaming -------------')

if __name__ == '__main__':
    SESSIONLIST = SessionList()
    ipcServerFactory = IpcServerFactory(SESSIONLIST)
    appProxyFactory = AppProxyFactory(SESSIONLIST)
