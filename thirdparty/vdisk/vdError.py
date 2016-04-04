class VdError(Exception):
    INVALID_TOKEN = 401

    def __init__(self, result):
        super(Exception, self).__init__()
        self.request = result['request']
        self.error_code = result['error_code']
        self.error_detail_code = result['error_detail_code']
        self.error = result['error']

