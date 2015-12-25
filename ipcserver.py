# -*- coding:utf-8 -*-
from twisted.web.resource import Resource
from twisted.internet.protocol import Factory, Protocol
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet import reactor, task
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
import time
from IpcPacket import *
from Session import *
import os





class IpcServer(Protocol):
    class InputPanel(object):
        def __init__(self, sessionList):
            self.sessionList = sessionList

        def setSessionList(self, sessionList):
            self.sessionList = sessionList
            print 'session see inputpanel %s' %(str(self.sessionList))

        def showSessionList(self):
            i = 0
            for session in self.sessionList.getAllSession():
                print '====  SESSIONS NO: %d -- %s ====' %(i, str(vars(session)))
                i += 1

        def showConversion(self):
            i = 0
            for session in self.sessionList.getAllSession():
                if session.conversion: 
                    print '====  CONVERSION NO: %d -- %s ====' %(i, str(vars(session.conversion)))
                i += 1

        def clearConversion(self, cameraId):
            if str(cameraId) == '1':
                print '==== CLEAR ALL CONVERSION ===='
                for session in self.sessionList.getAllSession():
                    session.conversion = None
            else:
                session = self.sessionList.getSessionByCamId(str(cameraId))
                session.conversion = None
                print '==== CLEAR CONVERSION IN CAMERA %s====' %(str(cameraId))

        def showInstruction(self):
            print '*** input(show session, show conversion, clear conversion seq): '

        def getNext(self, cmd):
            if cmd == 'show session':
                self.showSessionList()
            elif cmd == 'show conversion':
                self.showConversion()
            elif cmd.startswith('clear conversion'):
                cameraId = cmd.split()[-1]
                self.clearConversion(cameraId)



    def __init__(self, sessionList):
        self.sessionList = sessionList
        self.serverBuf = dict()
        self.sent = None
        self.inputPanel = IpcServer.InputPanel(None)

    def connectionLost(self, reason):
        #log.msg('connection Lost with: ' + str(self.session.cameraTransport))
        log.msg('reason is: ' + str(reason))
   
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))


    def activeSyncFile(self):
        for session in self.sessionList.getAllSession():
            for name in session.fileList:
                packet = GetFileCmdPacket(str(IpcPacket(NamePayload(name))))
                session.cameraPort.write(str(packet))
                log.msg('==== sync with camera %s for file %s ====' %(session.cameraId, name))

    def cameraConnected(self, cameraId, cameraPort):
        self.sessionList.addSession(cameraId, Session(cameraId, cameraPort))
        print 'server can see sessionlist', str(self.sessionList)
        self.inputPanel.setSessionList(self.sessionList)
        log.msg('==== camera %s connected=============' %(cameraId))
        if not os.path.exists('./cached/' + str(hash(cameraId))):
            os.system('mkdir %s' %('./cached/' +  str(hash(cameraId))))
        i = 0
        for session in self.sessionList.getAllSession():
            log.msg('ACTIVE SESSION: ' + str(i)  +'\t' + str(vars(session)))
            i += 1
        log.msg('====================================')
        cameraPort.write(str(HelloAckPacket(addHeader('', 0))))
        #syncTask = task.LoopingCall(self.activeSyncFile)
        #syncTask.start(60)

    def processFileListPacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)
        for port in session.getAllAppPorts():
            try:
                port.write(str(packet))
            except Exception as e:
                log.msg('Error in write to app port, %s' %(str(e)))
        #session.getActiveApp().write(str(packet))

        if session.conversion.unfinished is None:
            session.conversion.unfinished = packet.totalMsgSize
            session.conversion.cvsnBuf = ''
            with open('./namelist.log', 'a') as f:
                f.write('\n' + str(time.time()) + '\trequest file list')

        session.conversion.unfinished -= packet.payloadSize
        session.conversion.cvsnBuf += packet.payload

        if session.conversion.unfinished <= 0:
            for name in getFileListFromPayload(session.conversion.cvsnBuf):
                if name not in session.fileList:
                    session.fileList.append(name)
            with open('./namelist.log', 'a') as f:
                for name in session.fileList:
                    f.write(name+'\n')
                f.write('\n' + str(time.time()) + '\tfinish file list')
            session.conversion = None
            log.msg('=== %s has file %s ===' %(session.cameraId, str(session.fileList)))
            print '======= LIST Conversion CLOSED ========'

    def processFilePacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)
        for port in session.getAllAppPorts():
            try:
                port.write(str(packet))
            except Exception as e:
                log.msg('Error in write to app port, %s' %(str(e)))
        #time.sleep(0.01)
        #session.getActiveApp().write(str(packet))
        session.bandwidthTester.bandwithCalc(packet.payloadSize)
        filepath = './cached/' + str(hash(session.cameraId)) + '/' + session.conversion.filename + '.tmp'
        if session.conversion.unfinished is None:
            print '======== first file packet  ========'
            session.conversion.unfinished = packet.totalMsgSize
            with open(filepath, 'w') as f:
                f.write('')
        session.conversion.unfinished -= packet.payloadSize
        with open(filepath, 'a') as f:
            f.write(packet.payload)
        #print '======== %d B to be transported ========' %(session.conversion.unfinished)
        if session.conversion.unfinished <= 0:
            print '======== last file packet  ========'
            filepath = './cached/' + str(hash(session.cameraId)) + '/' + session.conversion.filename 
            renameCmd = 'mv %s.tmp %s' %(filepath, filepath)
            os.system(renameCmd) 
            session.conversion = None
            print '======= FILE Conversion CLOSED ========'

    def processStreamingPacket(self,packet, cameraPort):
        #print '========  streaming ========='
        session = self.sessionList.getSessionByCamPort(cameraPort)
        #time.sleep(0.01)
        session.bandwidthTester.bandwithCalc(packet.payloadSize)
        if len(session.getStreamingClient()) == 0:
            pass
            #print '======= app drop ports ========='
        else:
            for port in session.getStreamingClient():
                port.write(str(packet))

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

    def dataReceived(self, data):
        if not self.serverBuf.has_key(str(self.transport)):
            self.serverBuf[str(self.transport)] = ''
        self.serverBuf[str(self.transport)] += data
        packets, self.serverBuf[str(self.transport)] = getAllPacketFromBuf(self.serverBuf[str(self.transport)])
        if not packets:
            log.msg('NO PACKETS, but raw: %s' %(str(data)))
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
