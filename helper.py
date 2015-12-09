from twisted.internet import protocol, reactor
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet.protocol import Factory, Protocol
from twisted.logger import Logger
import sys, socket, os.path
import struct
log = Logger()

message = ''
domain = ''
appCmd = '\x55\xaa\x01' + '\x00' * 7 
getListCmd = appCmd + '\x01' + '\x00'
getFileCmd = appCmd + '\x02' + '\x00'
START_TAG = '\x55\xaa'

def getLengthFromHex(hexLengthStr):
    if len(hexLengthStr) == 4:
        return struct.unpack('!I', hexLengthStr)[0]
    else:
        return struct.unpack('!H', hexLengthStr)[0]

def getListFromMsg(message):
    '''
    if message[11] == '\x01':
        raise Exception('camera send error')
    '''
    startPos = message.find(START_TAG)
    fileList = list()
    while startPos != -1:
        listByteSize = getLengthFromHex(message[8:10])
        fileNum = listByteSize / 32
        for i in range(fileNum):
            fileI = slice(12 + i * 32, 12 + (i+1) * 32)
            fileList.append(message[fileI])
        message = message[startPos + 12 + listByteSize:]
        startPos = message.find(START_TAG)
    return fileList

def getMsgFrmPackt(LargePacket):
    MsgList = list()
    startPos = LargePacket.find(START_TAG)
    while startPos != -1:
        LargePacket = LargePacket[startPos:]
        packetLen = getLengthFromHex(LargePacket[8:10])
        MsgList.append(LargePacket[0:packetLen])
        LargePacket = LargePacket[packetLen:]
        startPos = LargePacket.find(START_TAG)
    return MsgList, LargePacket


with open('./MsgFrmCamera', 'r') as f:
    message = f.read()
result = getMsgFrmPackt(message)
print 'remain message: ', result[1]
for i in result[0]:
    for f in getListFromMsg(i):
        print str(f)




  
    def connectionMade(self):
	print ('connection made with: ' + str(self.transport.getPeer()))
	self.transport.write('what\'supguys~~')
        self.hasGetLength = False
        self.message = ''
        self.totalLength = 0

    def dataReceived(self, data):

        
        if self.hasGetLength == False:
            startPos = data.find(START_TAG)
            if startPos == -1:
                print 'Invalid data'
                return
            self.message += data[startPos:]
            self.totalLength = getLengthFromHex(data[4:8])
            self.hasGetLength = True
        else:
            self.message += data
        if self.isMessageComplete()[0] is True:
            print 'MESSAGE COMPLETE\n', 
            for f in getListFromMsg(self.message):
                print str(f)
            self.hasGetLength = 0
            self.message = ''
            self.totalLength = 0
        else:
            print 'MESSAGE UNCOMPLETE, total length %d, received %d ' %(self.totalLength, self.isMessageComplete()[1])
        

