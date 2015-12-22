#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

#from __future__ import print_function

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
import os.path
import time, random
from threading import Thread

from IpcPacket import *


def calc():
    timestamp = []
    size = []
    def calcRate(fileSize):
        if len(size) == 0:
            size.append(fileSize)
            timestamp.append(time.time())
        elif time.time() - timestamp[0] > 1:
            #print '==== Total Size %s ====' %(fileSize)
            result = (size[0]- fileSize) / float(time.time() - timestamp[0])
            size[0] = fileSize
            timestamp[0] = time.time()
            print 'RATE IS: ', result / 1024 / 1024 , ' MB/s'
    return calcRate

class InputPanel(object):
    def __init__(self, client, cameraPort):
        self.client = client
        self.cameraPort = cameraPort
        self.nameList = None
        self.appId = str(random.randint(100000, 999999))
    
    def getFile(self):
        if self.nameList is None:
            print 'file name list is none, please reqest list first'
            return
        seq = int(raw_input('input name seq: '))
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
        i = raw_input('input camera id, 0 or None is script camer, 1 is real camer')
        if str(i) == '0' or len(str(i)) == 0:
            helloPacket = HelloPacket(str(IpcPacket(addHeader(self.appId + '_890924', 13))))
        elif str(i) == '1':
            helloPacket = HelloPacket(str(IpcPacket(addHeader(self.appId + '_\x94\xa1\xa2:\x14\x00', 13))))
        self.cameraPort.write(str(helloPacket))

    def sendRawInput(self, i):
        print 'send raw data: ', i
        self.cameraPort.write(i)
        self.getNext()

    def getNext(self):
        cmd = raw_input('input next action(hello, file, list, connect, streaming):\n')
        if cmd == 'file':
            self.getFile()
        elif cmd == 'list':
            self.getFileList()
        elif cmd == 'connect' or len(cmd) == 0:
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
    def getInput(self, inputPanel):
        while True:
            print 'GET USER INPUT: '.center(40, '=')
            inputPanel.getNext()
            time.sleep(0.5)



    def __init__(self):
        self.buf = ''
        self.nameList = []
        self.fileSize = None
        self.calcRate = calc()
        self.fileBuf = list()
        self.fileName = ''
        self.streamSize= None
        self.streamStart= None
        self.inputThread = None

    def connectionMade(self):
        self.inputPanel = InputPanel(self, self.transport)


    def processFilePacket(self, packet):
        if self.fileSize is None:
            print '========= RECEIVINT FILE =============='
            self.fileSize = packet.totalMsgSize
        self.fileSize -= packet.payloadSize
        self.fileBuf.append(packet.payload)
        self.calcRate(self.fileSize)
        if self.fileSize == 0:
            self.fileSize = None
            with open('./video/' + self.fileName, 'w') as f:
                for buf in self.fileBuf:
                    f.write(buf)
                self.fileBuf = list()
            print '========= ALL FILE ACCEPTED =============='
            #self.inputPanel.getNext()

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
                print '=========== name list  ============'
                for name in getFileListFromPayload(packet.payload):
                    self.nameList.append(name)
                    print name
                self.inputPanel.setNameList(self.nameList)
                print '=========== All name list ============'
            elif isinstance(packet, VideoStreamingPacket):
                self.processVideoStreamingPacket(packet)


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
            if isinstance(packets[0], VideoStreamingPacket) or isinstance(packets[0], FilePacket):
                pass
            else:
                pass
                #self.inputPanel.getNext()
        else:
            print data
            if not self.inputThread:
                self.inputThread = Thread(target=self.getInput, args=(self.inputPanel,))
                self.inputThread.start() 
            #self.inputPanel.getNext()




class AppClientFactory(ClientFactory):
    protocol = AppClient

    def __init__(self):
        self.done = Deferred()


    def clientConnectionFailed(self, connector, reason):
        print('connection failed:', reason.getErrorMessage())
        self.done.errback(reason)


    def clientConnectionLost(self, connector, reason):
        print('connection lost:', reason.getErrorMessage())
        self.done.callback(None)



def main(reactor):
    domain = 'localhost'
    #domain = 'huahai'
    factory = AppClientFactory()
    reactor.connectTCP(domain, 8084, factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)
    print 'BLOCK IN TASK.REACT METHOD'
