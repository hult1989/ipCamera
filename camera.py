import os
import time
import socket
import collections

from twisted.python import log
from twisted.internet.protocol import Protocol, ClientFactory


from IpcPacket import buffer2packetStr, FileListPacket, FilePacket
from IpcPacket import FileErrPacket, VideoStreamingPacket, GetListCmdPacket
from IpcPacket import HelloPacket, IpcPacket, addHeader, getOnePacketFromBuf
from IpcPacket import generateFileListPayload, GetFileCmdPacket, GetStreamingPacket

#domain = 'huahai'
domain = 'localhost'
filepath = '/home/hult/Pictures'



def socketSendInPartial(sock, message):
    alreadySent = 0
    while alreadySent < len(message):
        sent = sock.send(message[alreadySent: alreadySent + 256])
        print 'socket send %d bytes' %(sent,)
        alreadySent += sent

def readFileToDictBuf(path):
    dictBuf = dict()
    for name in os.listdir(path):
        with open('/'.join((path, name))) as f:
            dictBuf[name] = f.read()
    with open('./video/mk9.mp4') as f:
        videoBuf = f.read()
        print 'Video:\t  {:>32}\tSize:{:>8}'.format('mk9.mp4', len(videoBuf))
    for name in dictBuf:
        print 'File name:{:>32}\tSize:{:>8}'.format(name, len(dictBuf[name]))
    return dictBuf, videoBuf


class Camera(Protocol):
    def __init__(self):
        self.buf = ''
        self.fileBuf , self.videoBuf = readFileToDictBuf(filepath)
        self.startStreaming = None

    def connectionMade(self):
        helloPacket = HelloPacket(str(IpcPacket(addHeader('Camera_890924', 13))))
        log.msg('send hello packet from Camera_890924')
        self.transport.write(str(helloPacket))

    def sendFileList(self):
        payload = generateFileListPayload(os.listdir(filepath))
        log.msg('response with file list')
        for packetStr in buffer2packetStr(payload):
            packet = FileListPacket(packetStr)
            self.transport.write(str(packet))

    def sendFile(self, name):
        log.msg('send file %s, size: %s' %(name, len(self.fileBuf[name])))
        if len(self.fileBuf[name]) != 0:
            for packetStr in buffer2packetStr(self.fileBuf[name]):
                self.transport.write(str(FilePacket(packetStr)))
        else:
            print 'length is zero, send file err packet'
            self.transport.write(str(FileErrPacket(addHeader('', 0))))
            #time.sleep(0.001)
        log.msg('file sent')

    def streaming(self):
        if not self.startStreaming:
            self.startStreaming = True
            print 'Video streaming request accepted, start streaming...'
        for packetStr in buffer2packetStr(self.videoBuf):
            if self.startStreaming:
                log.msg('streaming...')
                self.transport.write(str(VideoStreamingPacket(packetStr)))
                time.sleep(1)
            else:
                print 'Video Streaming canceled!'
                break
        print 'Video Streaming Finished!'
        self.startStreaming = None



    def processPacket(self, packet):
        if isinstance(packet, GetListCmdPacket):
            log.msg('recv get list packet')
            self.sendFileList()

        elif isinstance(packet, GetFileCmdPacket):
            name = packet.payload[:packet.payload.find('\x00')]
            log.msg('recv get file packet, request file %s' %(name))
            self.sendFile(name)

        elif isinstance(packet, GetStreamingPacket):
            self.streaming()

        elif isinstance(packet, CloseStreamingPacket):
            self.startStreaming = None
            print 'Streaming Canceled by APP client'

        elif isinstance(packet, HelloAckPacket):
            print 'server ack accepted, connected'



    def dataReceived(self,data):
        log.msg('RECEIVED RAW SIZE: %d' %(len(data)))
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
    import sys
    log.startLogging(sys.stdout)

    reactor.connectTCP(domain, 8083, CameraFactory())
    reactor.run()
