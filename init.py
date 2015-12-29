from twisted.web.server import Site
from twisted.python import log
from twisted.internet import reactor, stdio
from twisted.protocols import basic

from ipcserver import IpcServerFactory
from appproxy import AppProxyFactory
from Session import SessionList
from stdin import Echo
import sys




if __name__ == '__main__':
    sessionList = SessionList()
    ipcServerFactory = IpcServerFactory(sessionList)
    appProxyFactory = AppProxyFactory(sessionList)
    #stdio.StandardIO(Echo(ipcServerFactory.protocol.inputPanel))
    log.startLogging(open('./server.log', 'w'))
    #log.msg(sys.stdout)
    reactor.listenTCP(8083, ipcServerFactory)
    reactor.listenTCP(8084, appProxyFactory)
    reactor.run()
