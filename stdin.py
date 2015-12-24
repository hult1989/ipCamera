
# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


"""
An example of reading a line at a time from standard input
without blocking the reactor.
"""

from twisted.internet import stdio
from twisted.protocols import basic

class Echo(basic.LineReceiver):
    from os import linesep as delimiter
    def __init__(self, inputPanel):
        self.inputPanel = inputPanel

    def connectionMade(self):
        self.inputPanel.showInstruction()

    def lineReceived(self, line):
        self.inputPanel.showInstruction()
        self.inputPanel.getNext(line)

def main():
    stdio.StandardIO(Echo())
    from twisted.internet import reactor
    reactor.run()

if __name__ == '__main__':
    main()
