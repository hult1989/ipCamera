#!/usr/bin/env python
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

from __future__ import print_function

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.protocols.basic import LineReceiver
import os.path

import time


class EchoClient(Protocol):

    def connectionMade(self):
        self.transport.write("audio")



    '''
    def lineReceived(self, line):
        print("receive:", line)
        if line == self.end:
            self.transport.loseConnection()
    '''
    def dataReceived(self, data):
        with open('appRecvFile.mp3', 'a') as f:
            f.write(data)
        try:
            if os.path.getsize('./appRecvFile.mp3') >= 1096 * 1024:
                print ('ALL DATA GOT, total length: ' + str(os.path.getsize('./appRecvFile.mp3')))
        except:
            print ('FILE DOES EXIST')



class EchoClientFactory(ClientFactory):
    protocol = EchoClient

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
    factory = EchoClientFactory()
    reactor.connectTCP(domain, 8082, factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)
