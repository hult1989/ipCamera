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
            print '==== Total Size %s ====' %(fileSize)
            result = (fileSize - size[0]) / float(time.time() - timestamp[0])
            size[0] = fileSize
            timestamp[0] = time.time()
            print 'RATE IS: ', result / 1024 / 1024 , ' MB/s'
    return calcRate


class AppClient(Protocol):

    def __init__(self):
        self.buf = ''
        self.nameList = []
        self.totalSize = 0
        self.REQUEST_FILE = False
        self.REQUEST_LIST = False
        self.fileBuf = ''
        self.fileSize = None
        self.calcRate = calc()

    def connectionMade(self):
        appId = str(random.randint(100000, 999999))
        helloPacket = HelloPacket(str(IpcPacket(addHeader(appId + '_890924', 13))))
        self.transport.write(str(helloPacket))
        '''
        self.REQUEST_LIST = True
        '''
    def processPacket(self, packet, cameraPort):
        if isinstance(packet, FilePacket):
            while packet:
                if self.fileSize is None:
                    self.fileSize = 0
                self.fileSize += packet.payloadSize
                #print 'ACCEPTED: ', self.fileSize
                self.calcRate(self.fileSize)
                packet, self.buf = getOnePacketFromBuf(self.buf)

        elif isinstance(packet, FileListPacket):
            print '=========== name list  ============'
            while packet:
                for name in getFileListFromPayload(packet.payload):
                    self.nameList.append(name)
                    print name
                packet, self.buf = getOnePacketFromBuf(self.buf)
            print '=========== All name list ============'
            self.name = self.nameList[-1]
            packet = GetFileCmdPacket(str(IpcPacket(NamePayload(self.name))))
            cameraPort.write(str(packet))
            print '===send file request name: %s===' %(self.name)


    def checkProcess(self):
        print '=============== receievd %d B ============' %(len(self.buf) )

    def dataReceived(self, data):
        #print '====== received: %s ======' %(data,)
        self.buf += data
        #print '=== in app buf: %s ===' %(self.buf)
        packet, self.buf = getOnePacketFromBuf(self.buf)
        if packet:
            self.processPacket(packet, self.transport)
        elif data == IpcPacket.CONNECTED:
            print 'send filelist request'
            self.transport.write(str(GetListCmdPacket(addHeader('', 0))))
            return
        else:
            print data
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
    reactor.connectTCP(domain, 8082, factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)
