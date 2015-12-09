# -*- coding: utf-8 -*-
import sys, socket, os.path
import struct

domain = ''
appCmd = '\x55\xaa\x01' + '\x00' * 7 
getListCmd = appCmd + '\x01' + '\x00'
getFileCmd = appCmd + '\x02' + '\x00'


def getLengthFromHex(hexLengthStr):
    if len(hexLengthStr) == 4:
        return struct.unpack('!I', hexLengthStr)[0]
    else:
        return struct.unpack('!H', hexLengthStr[0])

def getListFromMsg(message):
    '''
    if message[11] == '\x01':
        raise Exception('camera send error')
    '''
    while message[0:2] != '\x55\xaa':
        message = message[1:]
    listByteSize = message[4:8]
    listByteSize = getLengthFromHex(listByteSize)
    print 'total list size is: ', listByteSize
    fileNum = listByteSize / 32
    print 'total file number is: ', fileNum
    for i in range(fileNum):
        fileI = slice(12 + i * 32, 12 + (i+1) * 32)
        print message[fileI]

'''
message = '\x55\xaa\x02\x00' + struct.pack('!I', 1 * 1024) + '\x00\x00' + '\x01\x00'
for i in range(32):
    message += 'good' + '\x64' * 28
'''

def sendOut(payload):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (domain, 8081)
    sock.connect(server_address)
    message = ''
    try:
        sock.sendall(payload)
        print 'request send out!\n'
        message += sock.recv(65536)
        print 'RECEIVED FIRST PACKET: ', message
        listPacketLength = getLengthFromHex(message[5:8])
        print 'TOTAL LENGTH: ', listPacketLength
        receivedLength = len(message)
        while receivedLength < listPacketLength:
            message += sock.recv(65536)
            receivedLength = len(message)
        return message
    except Exception as e:
        print e
    finally:
        sock.close()


'''
buf = bytearray(os.path.getsize('./pom.xml'))
with open('./pom.xml', 'rb') as f:
    f.readinto(buf)
sendOut(buf)
message = sendOut(getListCmd)    
print 'message received!\n'
print message
getListFromMsg(message)
'''

