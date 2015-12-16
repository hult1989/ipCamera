import os.path
import random
import struct

##############################################
class PayloadSizeError(Exception):
    def __init__(self, args=None):
        super(Exception, self).__init__(args)

class IllLegalPacket(Exception):
    def __init__(self, args=None):
        super(Exception, self).__init__(args)


#############################################
class IpcPacket(object):
    CONNECTED = 'camera connected'
    ERROR = '\x01'
    OK = '\x00'
    MSGHEAD = '\x55\xaa'
    def __init__(self, strMsg):
        if strMsg < 12:
            return None
        if strMsg.find(IpcPacket.MSGHEAD) == -1:
            return None
        strMsg = strMsg[strMsg.find(IpcPacket.MSGHEAD):]
        payloadsize = struct.unpack('!H', strMsg[8:10])[0]
        if payloadsize + 12 > len(strMsg):
            return None
        if payloadsize + 12 < len(strMsg):
            strMsg = strMsg[:payloadsize+12]

        self.version = strMsg[0:2]
        self.action = strMsg[2]
        self.isEncrypted = True if strMsg[3] == '\x01' else False
        self.totalMsgSize = struct.unpack('!I', strMsg[4:8])[0]
        self.payloadSize = struct.unpack('!H', strMsg[8:10])[0]
        self.cmd = strMsg[10]
        self.status = strMsg[11]
        self.payload = strMsg[12:]

    def __repr__(self):
        msg = self.version + self.action 
        msg += '\x01' if self.isEncrypted is True else '\x00'
        msg += struct.pack('!I', self.totalMsgSize)
        msg += struct.pack('!H', self.payloadSize)
        msg += self.cmd + self.status + self.payload
        return msg

    def __iter__(self):
        for s in vars(self).values:
            yield str(s)


class FileListPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x01'

    def getFileListFromPacket(self):
        if self.payloadSize != len(self.payload):
            raise PayloadSizeError
        fileCount = self.payloadSize / 32
        fileList = list()
        for i in range(fileCount):
            filename = self.payload[i*32: (i+1)*32]
            #print filename[:filename.find('\x00')]
            #yield str(filename)
            yield filename[:filename.find('\x00')]

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


class GetStreamingPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x01'
        self.cmd = '\x03'


class VideoStreamingPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x02'
        self.cmd = '\x03'

class HelloPacket(IpcPacket):
    def __init__(self, packet):
        IpcPacket.__init__(self, str(packet))
        self.action = '\x00'
        self.cmd = '\x00'


################################################################

def getFileList(path):
    '''return a list with file names'''
    result = []
    for name in os.listdir(path):
        result.append('/'.join((path, name)))
    return result


def generateFileSlice(buf):
    '''cut file into several pieces, each piece less than 1KB, yield file file pieces'''
    generated = 0
    while generated < len(buf):
        #pieceSize = 32 * random.randint(24, 32)
        pieceSize = 1 * 1024
        yield buf[generated: generated + pieceSize]
        generated += pieceSize

def addHeader(fileSlice, totalSize):
    result = '\x55\xaa\x00\x00' + struct.pack('!I', totalSize) + struct.pack('!H', len(fileSlice)) + '\x00' + '\x00' + fileSlice
    return result

def generatePacketWithHeader(filename):
    with open(filename) as f:
        buf = f.read()
    yield buffer2packets(buf)


def buffer2packets(buf):
    unfinished = len(buf)
    for fileSlice in generateFileSlice(buf):
        yield addHeader(fileSlice, unfinished)
        unfinished -= len(fileSlice)



def generateFileListPayload(namelist):
    payload = ''
    for name in namelist:
        #print 'ORGINAL FILE NAME IS: ', name
        assert len(name) < 32, 'NAME LENGTH ERROR ' + name
        if len(name) < 32:
            payload += name + '\x00' * (32 - len(name))
            #print 'name in payload is: ', payload[-32:]
    return payload

def getPacketFromFactory(strMsg):
    packet = IpcPacket(strMsg)
    if (packet.action =='\x00') and (packet.cmd == '\x00'):
        return HelloPacket(str(packet))
    elif packet.action == '\x01':
        if packet.cmd == '\x01':
            return GetListCmdPacket(str(packet))
        if packet.cmd == '\x02':
            return GetFileCmdPacket(str(packet))
    elif packet.action == '\x02':
        if packet.cmd == '\x01':
            return FileListPacket(str(packet))
        if packet.cmd == '\x02':
            return FilePacket(str(packet))

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
    try:
        start = buf.find(IpcPacket.MSGHEAD)
    except:
        return None, buf
    if (start == -1) or (start + 12 > len(buf)):
        return None, buf
    msgEnd  = start + struct.unpack('!H', buf[start+8:start+10])[0] + 12
    if msgEnd > len(buf):
        return None, buf
    return getPacketFromFactory(buf[start:msgEnd]), buf[msgEnd:]



if __name__ == '__main__':
    '''
    print 'ABOVE IS DIRECT READ FROM PAYLOAD==============='
    print 'BELOW IS READ FROM PAYLOAD======================'
    i = 0
    while i < len(payload) / 32:
        print payload[i*32: (1+i)*32]
        i += 1
    #print 'TOTAL PAYLOAD SIZE OF NANE LIST IS : ', len(payload)
    '''


    with open('./testMsg', 'r') as f:
        strMsg = f.read()
    strMsg = 'fafadsfasdfhalksdfsalkdhfasjkldfhsa;flj' + strMsg + 'tail' + strMsg + 'alsd'
    payload, strMsg = getPayloadFromBuf(strMsg)
    while payload:
        for name in getFileListFromPayload(payload):
            print name
        print '================== ALL PAYLOAD FINISHED =======================' 
        payload, strMsg = getPayloadFromBuf(strMsg)

    print '============LEFT TAIL=================='
    print 'TAIL LEFT: \t', strMsg
    print 'LEFT SIZE: \t', len(strMsg)

        

    


