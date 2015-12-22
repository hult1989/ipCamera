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
import os





class IpcServer(Protocol):
    def __init__(self, sessionList):
        self.sessionList = sessionList
        self.serverBuf = dict()
        self.sent = None

    def cameraConnected(self, cameraId, cameraPort):
        self.sessionList.addSession(cameraId, Session(cameraId, cameraPort))
        log.msg('==== camera %s connected=============' %(cameraId))
        if not os.path.exists('./cached/' + str(hash(cameraId))):
            os.system('mkdir %s' %('./cached/' +  str(hash(cameraId))))
        i = 0
        for session in self.sessionList.getAllSession():
            log.msg('ACTIVE SESSION: ' + str(i)  +'\t' + str(vars(session)))
            i += 1
        log.msg('====================================')
        cameraPort.write(str(HelloAckPacket(addHeader('', 0))))


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

    def processFileListPacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)
        session.getActiveApp().write(str(packet))
        if session.conversion.unfinished is None:
            session.conversion.unfinished = packet.totalMsgSize
            with open('./namelist.log', 'a') as f:
                f.write('\n' + str(time.time()) + '\trequest file list')
        session.conversion.unfinished -= packet.payloadSize
        with open('./namelist.log', 'a') as f:
            f.write(packet.payload[:packet.payload.find('\x00')])

        for name in getFileListFromPayload(packet.payload):
            if name not in session.fileList:
                session.fileList.append(name)
        #print '======== %d B to be transported ========' %(session.conversion.unfinished)
        if session.conversion.unfinished == 0:
            with open('./namelist.log', 'a') as f:
                f.write('\n' + str(time.time()) + '\tfinish file list')
            session.conversion = None
            log.msg('=== %s has file %s ===' %(session.cameraId, str(session.fileList)))

    def processFilePacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)
        #time.sleep(0.01)
        session.getActiveApp().write(str(packet))
        session.bandwidthTester.bandwithCalc(packet.payloadSize)
        filepath = './cached/' + str(hash(session.cameraId)) + '/' + session.conversion.filename
        if session.conversion.unfinished is None:
            print '======== first file packet  ========'
            session.conversion.unfinished = packet.totalMsgSize
            with open(filepath, 'w') as f:
                f.write('')
        session.conversion.unfinished -= packet.payloadSize
        with open(filepath, 'a') as f:
            f.write(packet.payload)
        #print '======== %d B to be transported ========' %(session.conversion.unfinished)
        if session.conversion.unfinished == 0:
            print '======== last file packet  ========'
            session.conversion = None
            print '======= Conversion CLOSED ========'

    def processStreamingPacket(self,packet, cameraPort):
        #print '========  streaming ========='
        session = self.sessionList.getSessionByCamPort(cameraPort)
        #time.sleep(0.01)
        if len(session.getStreamingClient()) == 0:
            print '======= app drop ports ========='
        else:
            for port in session.getStreamingClient():
                port.write(str(packet))
                session.bandwidthTester.bandwithCalc(packet.payloadSize)

    def processPacket(self, packets, cameraPort):
        for packet in packets:
            if isinstance(packet, HelloPacket):
                self.cameraConnected(packet.payload[7:], cameraPort)
            elif isinstance(packet, FileListPacket):
                self.processFileListPacket(packet, cameraPort)
            elif isinstance(packet, FilePacket):
                self.processFilePacket(packet, cameraPort)
            elif isinstance(packet, VideoStreamingPacket):
                self.processStreamingPacket(packet, cameraPort)

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
        packets, self.serverBuf[str(self.transport)] = getAllPacketFromBuf(self.serverBuf[str(self.transport)])
        if not packets:
            print data
        else:
            self.processPacket(packets, self.transport)





class IpcServerFactory(Factory):
    def __init__(self, sessionList):
        self.protocol = IpcServer(sessionList)

    def buildProtocol(self, addr):
        return self.protocol



if __name__ == '__main__':
    SESSIONLIST = SessionList()
    ipcServerFactory = IpcServerFactory(SESSIONLIST)
