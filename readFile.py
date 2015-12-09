import os.path
import random
import struct




def readToBuffer(filename):
    #buf = bytearray(os.path.getsize(filename))
    with open(filename, 'rb') as f:
        buf = f.read()
    return buf


def generateFileSlice(filename):
    buf = readToBuffer(filename)
    generated = 0
    while generated < len(buf):
        pieceSize = random.randint(512, 1412)
        yield buf[generated: generated + pieceSize]
        generated += pieceSize

def addMsgHeader(fileSlice, totalSize):
    result = '\x55\xaa\x02\x00' + struct.pack('!I', totalSize) + struct.pack('!H', len(fileSlice)) + '\x02' + '\x00' + fileSlice
    assert len(result) == len(fileSlice) + 12, 'ERROR HEADER'
    return result

def generateMsgWithHeader(filename):
    totalSize = os.path.getsize(filename)
    for fileSlice in generateFileSlice(filename):
        yield addMsgHeader(fileSlice, totalSize)

def getPacketsFromFile():
    for i in range(7):
        filename = './audio/file_' + str(i)
        for f in generateMsgWithHeader(filename):
            yield f




if __name__ == '__main__':
    with open('./TV.mp3', 'rb') as f:
        buf = f.read()
    with open('./testFile.mp3', 'w') as f:
        f.write(buf)

    '''
    count = 0
    size = 0
    for p in getPacketsFromFile():
        size += len(p)
        count += 1
    print count, size

    i = 0
    for f in generateFileSlice('./TV.mp3'):
        with open('./audio/file_' + str(i), 'w') as wf:
            wf.write(f)
        i += 1
    print i
            
    for i in range(7):
        with open('./audio/file_' + str(i), 'r') as rf:
            buf = bytearray(os.path.getsize('./audio/file_' + str(i)))
            rf.readinto(buf)
            with open('./tv.mp4', 'a') as wf:
                print 'write no. ', i, ' len: ', len(buf)
                wf.write(buf)

    '''
