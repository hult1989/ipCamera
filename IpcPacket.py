import os.path
import random
import struct

from common import IpcException


class IpcPacket(object):
    CONNECTED = 'camera connected'
    ERROR = '\x01'
    OK = '\x00'
    MSGHEAD = '\x55\xaa'
    HEADER_LENGTH = 12
    def __init__(self, strMsg):
        self.version = strMsg[0:2]
        self.action = strMsg[2]
        self.isEncrypted = True if strMsg[3] == '\x01' else False
        self.totalMsgSize = struct.unpack('!I', strMsg[4:8])[0]
        self.payloadSize = struct.unpack('!H', strMsg[8:10])[0]
        self.cmd = strMsg[10]
        self.status = strMsg[11]
        self.payload = strMsg[12:]

    def __str__(self):
        msg = self.version + self.action 
        msg += '\x01' if self.isEncrypted is True else '\x00'
        msg += struct.pack('!I', self.totalMsgSize)
        msg += struct.pack('!H', self.payloadSize)
        msg += self.cmd + self.status + self.payload
        return msg

    def __iter__(self):
        for s in vars(self).values:
            yield str(s)

class FileListErrPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x01'
        self.status = '\x01'


class FileListPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x01'

    def getFileListFromPacket(self):
        if self.payloadSize != len(self.payload):
            raise IpcPacket.PayloadSizeError
        fileCount = self.payloadSize / 32
        for i in range(fileCount):
            filename = self.payload[i*32: (i+1)*32]
            yield filename[:filename.find('\x00')]
    
    filenames = getFileListFromPacket

class GetListCmdPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x01'
        self.cmd = '\x01'

class GetFileCmdPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x01'
        self.cmd = '\x02'

class FilePacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x02'

class FileErrPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x02'
        self.status = '\x01'


class GetStreamingPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x01'
        self.cmd = '\x03'

class CloseStreamingPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x03'
        self.cmd = '\x04'

class VideoStreamingPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x03'

class HelloPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x21'

class HelloAckPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x04'
        self.cmd = '\x21'

class HelloErrPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x04'
        self.cmd = '\x21'
        self.status = '\x01'



################################################################


NamePayload = lambda name: addHeader(name + '\x00' * (32-len(name)), 32)


def addHeader(fileSlice, totalSize):
    result = '\x55\xaa\x00\x00' + struct.pack('!I', totalSize) + struct.pack('!H', len(fileSlice)) + '\x00' + '\x00' + fileSlice
    return result

def generatePacketWithHeader(filename):
    with open(filename) as f:
        buf = f.read()
    yield buffer2packetStr(buf)


def buffer2packetStr(buf):
    def generateFileSlice(buf):
        generated = 0
        while generated < len(buf):
            #pieceSize = 32 * random.randint(24, 32)
            pieceSize = 1 * 1024
            yield buf[generated: generated + pieceSize]
            generated += pieceSize

    unfinished = len(buf)
    for fileSlice in generateFileSlice(buf):
        yield addHeader(fileSlice, unfinished)
        unfinished -= len(fileSlice)



def generateFileListPayload(namelist):
    payload = ''
    for name in namelist:
        assert len(name) < 32, 'NAME LENGTH ERROR ' + name
        if len(name) < 32:
            payload += name + '\x00' * (32 - len(name))
    return payload

def getPacketFromFactory(strMsg):
    packet = IpcPacket(strMsg)
    if (packet.action =='\x04') and (packet.cmd == '\x21'):
        if packet.status == '\x00':
            return HelloAckPacket(str(packet))
        elif packet.status == '\x01':
            return HelloErrPacket(str(packet))
    elif (packet.action =='\x02') and (packet.cmd == '\x21'):
        return HelloPacket(str(packet))
    elif packet.action == '\x01':
        if packet.cmd == '\x01':
            return GetListCmdPacket(str(packet))
        elif packet.cmd == '\x02':
            return GetFileCmdPacket(str(packet))
        elif packet.cmd == '\x03':
            return GetStreamingPacket(str(packet))
    elif packet.action == '\x02':
        if packet.cmd == '\x01' and packet.status == '\x00':
            return FileListPacket(str(packet))
        if packet.cmd == '\x01' and packet.status == '\x01':
            return FileListErrPacket(str(packet))
        elif packet.cmd == '\x02' and packet.status == '\x00':
            return FilePacket(str(packet))
        elif packet.cmd == '\x02' and packet.status == '\x01':
            return FileErrPacket(str(packet))
        elif packet.cmd == '\x03':
            return VideoStreamingPacket(str(packet))
    elif packet.action == '\x03':
        if packet.cmd == '\x04':
            return CloseStreamingPacket(str(packet))

def getPayloadFromBuf(buf):
    packet, left = getOnePacketFromBuf(buf)
    if packet is None:
        return None, buf
    totalSize = struct.unpack('!I', str(packet)[4:8])[0]
    #print '============ FIRST PAYLOAD SIZE:\t%d ==========' %(totalSize)
    payload = ''
    payload += packet.payload
    while len(payload) < totalSize:
        packet, left = getOnePacketFromBuf(left)
        if not packet:
            break
        payload += packet.payload
    if len(payload) < totalSize:
        #print '===== unfinished payload, current size %d' %(len(payload))
        return None, buf
    return payload, left


def getFileListFromPayload(payload):
    while len(payload) > 0:
        yield payload[:payload.find('\x00')]
        payload = payload[32:]




def getOnePacketFromBuf(buf):
    start = buf.find(IpcPacket.MSGHEAD)
    if (start == -1) or (start + IpcPacket.HEADER_LENGTH > len(buf)):
        return None, buf
    
    payloadSize = struct.unpack('!H', buf[start+8:start+10])[0] 
    msgEnd = start + IpcPacket.HEADER_LENGTH + payloadSize
    if msgEnd > len(buf):
        return None, buf
    return getPacketFromFactory(buf[start:msgEnd]), buf[msgEnd:]


def getAllPacketFromBuf(buf):
    pkt, buf = getOnePacketFromBuf(buf)
    packets = []
    while pkt:
        packets.append(pkt)
        pkt, buf = getOnePacketFromBuf(buf)
    return (None, buf) if not packets else (packets, buf)



if __name__ == '__main__':

    with open('./test/testMsg', 'r') as f:
        strMsg = f.read()
    packets, buf = getAllPacketFromBuf(strMsg)
    p = packets[0]
    for p in p.filenames():
        print p


