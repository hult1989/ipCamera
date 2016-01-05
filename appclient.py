#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
import os.path
import time, random

from IpcPacket import *
from util.BandwidthTester import BandwidthTester
from twisted.internet import stdio
from twisted.protocols import basic



class InputPanel(object):
    def __init__(self, client, cameraPort):
        self.client = client
        self.cameraPort = cameraPort
        self.nameList = None
        #self.appId = str(random.randint(100000, 999999))
        self.appId = 'julian'

    def setCameraPort(self, cameraPort):
        self.cameraPort = cameraPort
    
    def getFile(self, seq):
        if self.nameList is None:
            print 'file name list is none, please reqest list first'
            return
        seq = int(seq)
        seq %= len(self.nameList)
        name = self.nameList[seq]
        self.client.fileName = name
        packet = GetFileCmdPacket(str(IpcPacket(NamePayload(name))))
        self.cameraPort.write(str(packet))
        print 'request file: ',name

    def getFileList(self):
        self.cameraPort.write(str(GetListCmdPacket(addHeader('', 0))))
        print 'request file list'

    def startVideoStreaming(self):
        packet = GetStreamingPacket(str(IpcPacket(addHeader('', 0))))
        self.cameraPort.write(str(packet))
        print 'request video streaming'
        
    def closeVideoStreaming(self):
        packet = CloseStreamingPacket(str(IpcPacket(addHeader('', 0))))
        self.cameraPort.write(str(packet))
        print 'close video streaming'

    def setNameList(self, nameList):
        self.nameList = nameList

    def connectToCamera(self):
        helloPacket = HelloPacket(str(IpcPacket(addHeader(self.appId + '_\x94\xa1\xa2:\x14\x6b', 13))))
        #helloPacket = HelloPacket(str(IpcPacket(addHeader(self.appId + '_890924', 13))))
        self.cameraPort.write(str(helloPacket))

    def sendRawInput(self, i):
        print 'send raw data: ', i
        self.cameraPort.write(i)

    def showInstruction(self):
        print 'input some cmd: '


    def getNext(self, cmd):
        if cmd.startswith('file'):
            self.getFile(cmd.split()[1])
        elif cmd == 'list':
            self.getFileList()
        elif cmd == 'connect':
            self.connectToCamera()
        elif cmd == 'streaming':
            self.startVideoStreaming()
        elif cmd == 'close':
            self.closeVideoStreaming()
        elif cmd == 'exit':
            exit()
        else:
            self.sendRawInput(cmd)

class AppClient(Protocol):
    def __init__(self):
        self.buf = ''
        self.fileBuf = None
        self.nameList = []
        self.fileSize = None
        self.fileName = ''
        self.streamSize= None
        self.streamStart= None
        self.inputPanel = InputPanel(self, None)
        self.tester = None

    def connectionMade(self):
        self.inputPanel.setCameraPort(self.transport)


    def processFilePacket(self, packet):
        if self.fileSize is None:
            self.fileBuf = list()
            print '========= RECEIVINT FILE =============='
            self.fileSize = packet.totalMsgSize
            self.tester = BandwidthTester()
        self.fileSize -= packet.payloadSize
        self.fileBuf.append(packet.payload)
        self.tester.bandwithCalc(packet.payloadSize)
        if self.fileSize == 0:
            self.fileSize = None
            self.tester = None
            for buf in self.fileBuf:
                print buf
            '''
            with open('./video/' + self.fileName, 'w') as f:
                for buf in self.fileBuf:
                    f.write(buf)
                self.fileBuf = list()
            '''
            self.fileBuf = None
            print '========= ALL FILE ACCEPTED =============='

    def processListPacket(self, packet):
        if self.fileSize is None:
            self.nameList = list()
            self.fileBuf = ''
            print '========= RECEIVINT LIST =============='
            self.fileSize = packet.totalMsgSize
        self.fileSize -= packet.payloadSize
        self.fileBuf += packet.payload
        if self.fileSize == 0:
            self.fileSize = None
            for name in getFileListFromPayload(self.fileBuf):
                print name
                self.nameList.append(name)
            self.fileBuf = None
            self.inputPanel.setNameList(self.nameList)
            print '========= ALL LIST ACCEPTED =============='

    def processVideoStreamingPacket(self, packet):
        now = time.time()
        if self.streamStart is None:
            self.streamStart = now
            self.streamSize = 0
        self.streamSize += packet.payloadSize
        if now - self.streamStart > 1:
            print '====== Streaming Rate: %.4f MB/s =======' %((self.streamSize)/(now-self.streamStart)/float(1024* 1024))
            self.streamSize = 0
            self.streamStart = now



    def processPacket(self, packetList, cameraPort):
        for packet in packetList:
            if isinstance(packet, FilePacket):
                self.processFilePacket(packet)
            elif isinstance(packet, FileListPacket):
                self.processListPacket(packet)
            elif isinstance(packet, VideoStreamingPacket):
                self.processVideoStreamingPacket(packet)
            elif isinstance(packet, HelloAckPacket):
                print '===== ack recevied from server, connected with server ===='
            elif isinstance(packet, HelloErrPacket):
                print '===== target camera not online ===='
            elif isinstance(packet, FileListErrPacket):
                print '==== %s ====' %(packet.payload)


    def checkProcess(self):
        print '=============== receievd %d B ============' %(len(self.buf) )

    def dataReceived(self, data):
        #print '====== received: %s ======' %(data,)
        self.buf += data
        #print '=== in buf size: %s ===' %(len(self.buf))
        packets, self.buf = getAllPacketFromBuf(self.buf)
        time.sleep(0.01)
        if packets:
            self.processPacket(packets, self.transport)
        else:
            print data


class AppClientFactory(ClientFactory):
    def buildProtocol(self, addr):
        return self.protocol

    def __init__(self):
        self.done = Deferred()
        self.protocol = AppClient()

    def clientConnectionFailed(self, connector, reason):
        print('connection failed:', reason.getErrorMessage())
        self.done.errback(reason)


    def clientConnectionLost(self, connector, reason):
        print('connection lost:', reason.getErrorMessage())
        self.done.callback(None)



def main(reactor):
    #domain = 'localhost'
    domain = 'huahai'
    from stdin import Echo
    factory = AppClientFactory()
    reactor.connectTCP(domain, 8084, factory)
    stdio.StandardIO(Echo(factory.protocol.inputPanel))
    return factory.done



if __name__ == '__main__':
    task.react(main)
