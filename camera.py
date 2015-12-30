import socket
from twisted.internet.protocol import Protocol, ClientFactory
import os, time



from  IpcPacket import *

domain = 'huahai'
#domain = 'localhost'

def socketSendInPartial(sock, message):
    alreadySent = 0
    while alreadySent < len(message):
        sent = sock.send(message[alreadySent: alreadySent + 256])
        print 'socket send %d bytes' %(sent,)
        alreadySent += sent

def readFileToDictBuf(path):
    dictBuf = dict()
    for name in getFileList(path):
        with open('/'.join((path, name))) as f:
            dictBuf[name] = f.read()
    with open('./audio/mk9.mp4') as f:
        videoBuf = f.read()
        print 'video: mk9.mp4, buf size: ', len(videoBuf)
    return dictBuf, videoBuf


class Camera(Protocol):
    def __init__(self):
        self.buf = ''
        self.fileBuf , self.videoBuf = readFileToDictBuf('audio')
        for name in self.fileBuf:
            print 'File name: %s , Size: %s' %(name, len(self.fileBuf[name]))
        self.startStreaming = None

    def connectionMade(self):
        helloPacket = HelloPacket(str(IpcPacket(addHeader('Camera_890924', 13))))
        print 'Send data:  ', str(helloPacket)[12:]
        self.transport.write(str(helloPacket))

    def processPacket(self, packet):
        if isinstance(packet, GetListCmdPacket):
            payload = generateFileListPayload(getFileList('audio'))
            print 'response with file list'
            #time.sleep(10)
            for packetStr in buffer2packets(payload):
                packetStr = str(FileListPacket(packetStr))
                self.transport.write(packetStr)
        elif isinstance(packet, GetFileCmdPacket):
            name = packet.payload[:packet.payload.find('\x00')]
            print name, ' response with file request, len: ', len(self.fileBuf[name])
            for packetPayload in buffer2packets(self.fileBuf[name]):
                packetPayload = str(FilePacket(packetPayload))
                self.transport.write(packetPayload)
                #time.sleep(0.001)
            print 'all file sended!'
        elif isinstance(packet, GetStreamingPacket):
            if not self.startStreaming:
                self.startStreaming = True
                print 'Video streaming request accepted, start streaming...'
            #while self.startStreaming:
            for packet in buffer2packets(self.videoBuf):
                if self.startStreaming:
                    packet = str(VideoStreamingPacket(packet))
                    self.transport.write(packet)
                    #time.sleep(0.001)
                else:
                    print 'Video Streaming canceled!'
                    break
            print 'Video Streaming Finished!'
            self.startStreaming = None
        elif isinstance(packet, CloseStreamingPacket):
            self.startStreaming = None
            print 'Streaming Canceled by APP client'
        elif isinstance(packet, HelloAckPacket):
            print 'server ack accepted, connected'



    def dataReceived(self,data):
        print data
        self.buf += data
        packet, self.buf = getOnePacketFromBuf(self.buf)
        while packet:
            self.processPacket(packet)
            packet, self.buf = getOnePacketFromBuf(self.buf)

        

            
class CameraFactory(ClientFactory):
    def startedConnecting(self, connector):
        print 'started to connect'
        #print 'CONNECTOR IS: ', vars(connector)


    def buildProtocol(self, addr):
        return Camera()

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection, reason: ', reason

    def clientConnectionFailed(self, connector, reason):
        print 'connect %s failed, reason: %s ' %(str(connector), str(reason))

if __name__ == '__main__':
    from twisted.internet import reactor
    reactor.connectTCP(domain, 8083, CameraFactory())
    reactor.run()
