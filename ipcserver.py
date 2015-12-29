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
        self.syncTask = task.LoopingCall(self.activeSyncFile)

    def connectionLost(self, reason):
        #log.msg('connection Lost with: ' + str(self.session.cameraTransport))
        log.msg('reason is: ' + str(reason))
   
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))


    def activeSyncFile(self):
        for session in self.sessionList.getAllSession():
            if not session:
                continue
            if len(session.fileList) == 0:
                session.cameraPort.write(str(GetListCmdPacket(addHeader('', 0))))
                return
            if FileStatus.PENDING in session.fileList.values():
                print  ('camera %s busy, some file in transmission' %(session.cameraId))
                continue
            for name in session.fileList:
                if session.fileList[name] == FileStatus.NXIST:
                    print 'REQUEST FILE %s' %(name,)
                    session.cameraPort.write(str(GetFileCmdPacket(NamePayload(name))))
                    session.fileList[name] = FileStatus.PENDING
                    assert name == session.getPendingName(), 'PENDING NAME ERROR!!!'
                    break

                '''

                packet = GetFileCmdPacket(str(IpcPacket(NamePayload(name))))
                session.cameraPort.write(str(packet))
                log.msg('==== sync with camera %s for file %s ====' %(session.cameraId, name))
                '''

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

    def processFileListPacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)

        if session.sessBuf is None:
            session.sessBuf = ''
            session.unfinished = packet.totalMsgSize
            with open('./namelist.log', 'a') as f:
                f.write('\n[ ' + str(time.time()) + ' ]  server request file list')

        session.unfinished -= packet.payloadSize
        session.sessBuf += packet.payload

        if session.unfinished <= 0:
            for name in getFileListFromPayload(session.sessBuf):
                if not name.endswith('MP4'):
                    continue
                if name not in session.fileList:
                    if not os.path.exists('/'.join(('./cached' , str(hash(session.cameraId)),  name))):
                        session.fileList[name] = FileStatus.NXIST
                    else:
                        session.fileList[name] = FileStatus.EXIST
            with open('./namelist.log', 'a') as f:
                for name in session.fileList:
                    f.write(name+'\n')
                f.write('\n[ ' + str(time.time()) + ' ] finish file list')
            session.sessBuf = None
            session.unfinished = None
            log.msg('=== %s has file %s ===' %(session.cameraId, str(session.fileList)))
            print '======= LIST Conversion CLOSED ========'

    def processFilePacket(self, packet, cameraPort):
        session = self.sessionList.getSessionByCamPort(cameraPort)
        #time.sleep(0.01)
        #session.getActiveApp().write(str(packet))
        session.bandwidthTester.bandwithCalc(packet.payloadSize)
        filepath = './cached/' + str(hash(session.cameraId)) + '/' + session.getPendingName() + '.tmp'
        if session.unfinished is None:
            print '======== first file packet  ========'
            session.unfinished = packet.totalMsgSize
            session.sessBuf = list()
        session.unfinished -= packet.payloadSize
        session.sessBuf.append(packet.payload)
        #print '======== %d B to be transported ========' %(session.conversion.unfinished)
        if session.unfinished <= 0:
            print '======== last file packet  ========'
            filepath = './cached/' + str(hash(session.cameraId)) + '/' + session.getPendingName()
            with open(filepath, 'w') as f:
                for p in session.sessBuf:
                    f.write(p)
            session.unfinished = None
            session.sessBuf = None
            session.fileList[session.getPendingName()] = FileStatus.EXIST
            assert session.getPendingName() is None, 'status ERROR in %s' %(session.getPendingName())
            print '======= FILE Conversion CLOSED ========'
            log.msg('=== %s has file %s ===' %(session.cameraId, str(session.fileList)))

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

    def processHelloPacket(self, packet, cameraPort):
        self.cameraConnected(packet.payload[7:], cameraPort)
        #cameraPort.write(str(GetListCmdPacket(addHeader('', 0))))
        self.syncTask.start(5)

    def processPacket(self, packets, cameraPort):
        for packet in packets:
            if isinstance(packet, HelloPacket):
                self.processHelloPacket(packet, cameraPort)
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
            temp = list()
            for c in data:
                temp.append(hex(ord(c)))
            log.msg('NO PACKETS, but raw: %s' %(str(temp)))
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
