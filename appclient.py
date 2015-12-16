#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

#from __future__ import print_function

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
import os.path
import time

from IpcPacket import *


class AppClient(Protocol):

    def __init__(self):
        self.buf = ''
        self.nameList = []
        self.totalSize = 0
        self.REQUEST_FILE = False
        self.REQUEST_LIST = False
        self.fileBuf = ''
        self.fileSize = None

    def connectionMade(self):
        self.transport.write(str(GetListCmdPacket(addHeader('', 0))))
        self.REQUEST_LIST = True

    def checkProcess(self):
        print '=============== receievd %d B ============' %(len(self.buf) )

    def dataReceived(self, data):
        NamePayload = lambda name: addHeader(name + '\x00' * (32-len(name)), 32)
        #print '==================  RECEIVED DATA LENGTH  %d  =====================' %(len(data,))
        self.checkProcess()
        if self.REQUEST_LIST:
            self.buf += data
            payload, self.buf = getPayloadFromBuf(self.buf)
            if not payload:
                #print 'One File not finished'
                return
            print '=============== File finished ================'
            for name in getFileListFromPayload(payload):
                print name
                self.nameList.append(name)
            self.name = '011.BMP'
            #self.name = self.nameList[-1]
            packet = GetFileCmdPacket(str(IpcPacket(NamePayload(self.name))))
            self.transport.write(str(packet))
            print '===send file request!==='
            print str(self.name)
            self.REQUEST_FILE = True
            self.REQUEST_LIST = False
        elif self.REQUEST_FILE:
            self.buf += data
            packet, self.buf = getOnePacketFromBuf(self.buf)
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
    #domain = 'localhost'
    domain = 'huahai'
    factory = AppClientFactory()
    reactor.connectTCP(domain, 8082, factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)
