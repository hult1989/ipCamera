from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor, task
from sys import stdout
import random

class Echo(Protocol):
    def dataReceived(self, data):
        stdout.write(data)

class EchoFactory(ClientFactory):
    def __init__(self):
        self.echo = Echo()

    def startConnecting(self, connector):
        print 'trying to connect'

    def buildProtocol(self, addr):
        print 'connected'
        return self.echo

def connectionWrite(factories):
    fid = random.randint(0, 9)
    try:
        factories[fid].echo.transport.write(str(fid))
    except Exception as e:
        print e


if __name__ == '__main__':
    factories = [EchoFactory() for _ in range(10)]
    for i in range(10):
        reactor.connectTCP('localhost', 8080, factories[i])
    task.LoopingCall(connectionWrite, factories).start(2)
    reactor.run()
