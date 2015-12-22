import time
class BandwidthTester(object):
    def __init__(self):
        self.startTime = 0
        self.totalSize = 0

    def bandwithCalc(self, size):
        self.totalSize += size
        now = time.time()
        if (now - self.startTime) > 1:
            print '***** CURRENT RATE: %d KB/s *****' %(self.totalSize/(now - self.startTime)/1024)
            self.startTime = now
            self.totalSize = 0


if __name__ == '__main__':
    tester = BandwidthTester()
    for i in range(10):
        tester.bandwithCalc(1024)
        time.sleep(0.5)


