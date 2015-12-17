import socket
from twisted.internet.protocol import Protocol, ClientFactory
import os



from  IpcPacket import *

#domain = 'huahai'
domain = 'localhost'

def socketSendInPartial(sock, message):
    alreadySent = 0
    while alreadySent < len(message):
        sent = sock.send(message[alreadySent: alreadySent + 256])
        print 'socket send %d bytes' %(sent,)
        alreadySent += sent

def readFileToDictBuf(path):
    dictBuf = dict()
    for name in getFileList(path):
        with open(name) as f:
            dictBuf[name] = f.read()
            print name, ' ', len(dictBuf[name])
    return dictBuf


class Camera(Protocol):
    def __init__(self):
        self.buf = ''
        self.fileBuf = readFileToDictBuf('audio')
        for name in self.fileBuf:
            print 'File name: %s , Size: %s' %(name, len(self.fileBuf[name]))

    def connectionMade(self):
        helloPacket = HelloPacket(str(IpcPacket(addHeader('alice', 5))))
        print 'Send data:  ', str(helloPacket)
        self.transport.write(str(helloPacket))

    def processPacket(self, packet):
        if isinstance(packet, GetListCmdPacket):
            payload = generateFileListPayload(getFileList('audio'))
            print 'response with file list'
            for packetStr in buffer2packets(payload):
                packetStr = str(FileListPacket(packetStr))
                self.transport.write(packetStr)
        elif isinstance(packet, GetFileCmdPacket):
            name = packet.payload[:packet.payload.find('\x00')]
            print name, ' response with file request, len: ', len(self.fileBuf[name])
            for packetPayload in buffer2packets(self.fileBuf[name]):
                packetPayload = str(FilePacket(packetPayload))
                self.transport.write(packetPayload)
            print 'all file sended!'



    def dataReceived(self,data):
        print data
        self.buf += data
        packet, self.buf = getOnePacketFromBuf(self.buf)
        if not packet:
            return
        self.processPacket(packet)

        '''
        se
        if isinstance(packet, GetListCmdPacket):
                    elif isinstance(packet, GetFileCmdPacket):
            name = packet.payload[:packet.payload.find('\x00')]
            #print name, ' response with app request, file len: ', len(self.fileBuf[name])
            for packetPayload in buffer2packets(self.fileBuf[name]):
                packetPayload = str(FilePacket(packetPayload))
                self.transport.write(packetPayload)
                #print 'send file slice, packet len: ', len(packetPayload)
            #print 'all file sended!'
        #elif isinstance(packet, GetStreamingPacket):
        '''



            
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
