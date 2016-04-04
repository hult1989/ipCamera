class PayloadSizeError(Exception):
    def __init__(self, args=None):
        super(PayloadSizeError, self).__init__(args)

class IllLegalPacket(Exception):
    def __init__(self, args=None):
        super(IllLegalPacket, self).__init__(args)

