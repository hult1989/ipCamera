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
    REQUEST_FILE = False
    REQUEST_LIST = False

    def __init__(self):
        self.buf = ''
        self.nameList = []
        self.totalSize = 0

    def connectionMade(self):
        self.transport.write(str(GetListCmdPacket(addHeader('', 0))))
        self.REQUEST_LIST = True

    def dataReceived(self, data):
        NamePayload = lambda name: addHeader(name + '\x00' * (32-len(name)), 32)
        #print '==================  RECEIVED DATA LENGTH  %d  =====================' %(len(data,))
        if self.REQUEST_LIST:
            self.buf += data
            packet, self.buf = getOnePacketFromBuf(self.buf)
            while packet is not None:
                for name in packet.getFileListFromPacket():
                    print name
                    self.nameList.append(name)
                packet, self.buf = getOnePacketFromBuf(self.buf)
            #print '===All packet received!==='
            packet = GetFileCmdPacket(str(IpcPacket(NamePayload(self.nameList[-1]))))
            print '===send file request!==='
            print str(packet)
            self.transport.write(str(packet))
            self.REQUEST_FILE = True
            self.REQUEST_LIST = False
        elif self.REQUEST_FILE:
            self.buf += data
            self.totalSize += len(data)
            packet, self.buf = getOnePacketFromBuf(self.buf)
            while packet is not None:
                if packet.action == '\x02' and packet.cmd == '\x02':
                    with open('./appCache', 'a') as f:
                        f.write(packet.payload)
                        #print 'add to file, len: ', len(packet.payload), ' ', packet.payloadSize
                packet, self.buf = getOnePacketFromBuf(self.buf)
            if self.totalSize /1024 % 1024 < 100:
                print '===video received %.2f MB ===' %(self.totalSize/ 1024/1024,)
            

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
