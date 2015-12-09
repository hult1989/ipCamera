from twisted.web.server import Site
from twisted.python import log
from twisted.internet import reactor

from ipcserver import appProxyFactory, ipcServerFactory
import sys




if __name__ == '__main__':
    import sys
    log.startLogging(open('./server.log', 'w'))
    #log.msg(sys.stdout)
    reactor.listenTCP(8081, ipcServerFactory)
    reactor.listenTCP(8082, appProxyFactory)
    reactor.run()