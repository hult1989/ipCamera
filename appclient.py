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
        elif cmd == 'exit':
            exit()
        else:
            self.sendRawInput(cmd)

class AppClient(Protocol):

    def __init__(self):
        self.buf = ''
        self.nameList = []
        self.fileSize = None
        self.calcRate = calc()
        self.fileBuf = list()
        self.fileName = ''

    def connectionMade(self):
        self.inputPanel = InputPanel(self, self.transport)

    def processFilePacket(self, packet):
        if self.fileSize is None:
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
            self.inputPanel.getNext()

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


    def checkProcess(self):
        print '=============== receievd %d B ============' %(len(self.buf) )

    def dataReceived(self, data):
        #print '====== received: %s ======' %(data,)
        self.buf += data
        #print '=== in buf size: %s ===' %(len(self.buf))
        packets, self.buf = getAllPacketFromBuf(self.buf)
        if packets:
            self.processPacket(packets, self.transport)
        else:
            print data
        if self.fileSize is None:
            self.inputPanel.getNext()
        '''
        self.checkProcess()
            while packet:
                if not self.fileSize:
                    self.fileSize = packet.totalMsgSize
                self.fileBuf += packet.payload
                packet, self.buf = getOnePacketFromBuf(self.buf)
            if len(self.fileBuf) < self.fileSize:
                print 'Accept Packet, totalSize: %d, current size: %d' %(self.fileSize, len(self.buf))
            elif self.fileSize == len(self.fileBuf):
                with open('video/' +  self.name, 'a') as f:
                    print 'wirte to file: %s' %( self.name)
                    print '===== all file received, total length %d ===========' %(self.fileSize,)
                    f.write(self.fileBuf)
                    self.fileBuf = ''
                    self.fileSize = None
        ''' 

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
