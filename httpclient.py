import httplib
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver



domain = 'localhost'
host = domain + ':8082'

def httpRequest(requestBody, url, method='POST'):
    con = httplib.HTTPConnection(domain, 8082)
    con.request(method, url, requestBody)
    result = con.getresponse().read()
    con.close()
    print result

class EchoClient(LineReceiver):
    end = "Bye-bye!"

    def connectionMade(self):
        self.sendLine("audio")


    '''
    def lineReceived(self, line):
        print("receive:", line)
        if line == self.end:
            self.transport.loseConnection()
    '''
    def dataReceived(self, data):
        with open('./audiofile', 'a') as f:
            f.write(data)
        




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
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', 8082, factory)
    return factory.done



if __name__ == '__main__':
    task.react(main)

    #httpRequest('hi, camera~~', '/')
