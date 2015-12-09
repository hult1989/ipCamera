import socket
from twisted.internet.protocol import Protocol, ClientFactory
#domain = 'huahai'
domain = 'localhost'
from readFile import getPacketsFromFile, generateFileSlice

def socketSendInPartial(sock, message):
    alreadySent = 0
    while alreadySent < len(message):
        sent = sock.send(message[alreadySent: alreadySent + 256])
        print 'socket send %d bytes' %(sent,)
        alreadySent += sent


'''
with open('./testMsg', 'r') as f:
    message = f.read()

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_address = (domain, 8081)
sock.connect(server_address)
socketSendInPartial(sock, message)
sock.close()

'''

class Camera(Protocol):

    def dataReceived(self,data):
        if data.strip() == 'audio':
            print ('REVEIVED SIG, GONA READFILE')
            try:
                for p in generateFileSlice('./TV.mp3'):
                    print 'Send video clip, length: ', len(p)
                    self.transport.write(p)
                print 'FINISH SENDING ALL FILE!!!!'
                self.transport.loseConnection()
            except Exception as e:
                print e
                self.transport.loseConnection()
        else:
            self.transport.write('camers received: %s' %(data,))


class CameraFactory(ClientFactory):
    def startedConnecting(self, connector):
        print 'started to connect'
        #print 'CONNECTOR IS: ', vars(connector)


    def buildProtocol(self, addr):
        print 'connected!!'
        return Camera()

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection, reason: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connect %s failed, reason: %s ' %(str(connector), str(reason))

if __name__ == '__main__':
    from twisted.internet import reactor
    reactor.connectTCP(domain, 8081, CameraFactory())
    reactor.run()
