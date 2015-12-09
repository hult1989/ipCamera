from twisted.internet import protocol, reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory, Protocol

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        with open('./appReceivedFile.mp3', 'a') as f:
            f.write(data)
        

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()


server = TCP4ServerEndpoint(reactor, 8082);
server.listen(EchoFactory())
reactor.run()
