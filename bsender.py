# -*- coding: utf-8 -*-
import sys, socket, os.path

domain = 'localhost'


size= os.path.getsize('./TV.mp3')
buf = bytearray(os.path.getsize('./TV.mp3'))
def sendOut():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (domain, 8082)
    sock.connect(server_address)
    sock.send('something test\r\n')
    sock.send('audio')
    print 'file no: ', sock.fileno()
    try:
        recvd = 0
        while recvd < size:
            data = sock.recv(65535)
            print 'recv data size:\t', len(data)
            recvd += len(data)
            buf += data
        print 'ALL DATA RECEIVED, TOTAL LEN: ', len(buf)
    except Exception as e:
        print e
    finally:
        sock.close()



    
if __name__ == '__main__':
    sendOut()

