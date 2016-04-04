from twisted.internet.protocol import Factory, Protocol
from twisted.internet import defer, reactor, task
from twisted.python import log
import time
import sys

from connectionmanager import ConnectionManager



class Server(Protocol):
    def __init__(self, manager):
        self.cManager = manager

    def connectionMade(self):
        self.cManager.newDeviceConnected(self.transport)
        print self.cManager.historicalNum

    def connectionLost(self, reason):
        self.cManager.removePort(self.transport)

    def dataReceived(self, data):
        con = self.cManager.validConnections[self.transport]
        con.recvData(data)
        print 'receive %s from %s' %(data, self.transport.client)

class ServerFactory(Factory):
    def __init__(self, manager):
        self.cManager = manager

    def buildProtocol(self, addr):
        return Server(self.cManager)

if __name__ == '__main__':
    import sys
    log.startLogging(sys.stdout)
    manager = ConnectionManager()
    reactor.listenTCP(8080, ServerFactory(manager))
    task.LoopingCall(manager.closeIdleConnection).start(2)
    reactor.run()

