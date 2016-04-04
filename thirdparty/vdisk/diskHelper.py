import json
import time
from vdisk import OAuth2, Client, Response
from vdError import VdError

class VdiskHelper(object):
    app_key = '1984610354'
    app_secret = 'a35aecd0d36ac45dda1c03f98e992b90'
    call_back_url = 'http://116.7.225.58:8082'
    
    def __init__(self):
        self.oauth = OAuth2(self.app_key, self.app_secret, self.call_back_url)
        self.ipc = Client('sandbox')

    def getAccessToken(self):
        with open('./token.txt') as f:
            t = f.read()
        t = eval(t)
        #print 'CURRENT TIME %s, token expires in %s' %(time.time(), t['expires_in'])
        if time.time() < t['expires_in'] - 600:
            print 'access token not expires'
            return t['access_token']
        else:
            print 'access token expires'
            result = self.oauth.access_token(grant_type='refresh_token', refresh_token=t['refresh_token'])
            result = eval(result)
            if 'code' in result:
                raise Exception(str(result))
            t['expires_in'] = result['expires_in']
            t['access_token'] = result['access_token'].strip()
            t['refresh_token'] = result['refresh_token'].strip()
            with open('./token.txt','w') as f:
                f.write(str(t))
            return t['access_token']
            
    def processResult(result):
        result = eval(result.read())
        if not 'error' in result:
            print json.dumps(result, indent=4)


    def freshToken(self):
        token = self.getAccessToken()
        result = eval(self.ipc.metadata(token, ''))
        if not 'error' in result:
            print 'token valid'
            return True
        print 'token not valid'



            
            

     
def printResult(result):
    print '---------------------'
    try:
        result = json.loads(result.read())
        print json.dumps(result, indent=4)

    except Exception as e:
        #print json.dumps(eval(result), indent=4)
        print e

   


if __name__ == '__main__':
    helper = VdiskHelper()
    try:
        token = helper.getAccessToken()
        ipc = Client('sandbox')
        print token
        result = ipc.metadata(token, '')
        printResult(result)

    except Exception as e:
        print json.dumps(eval(e.message), indent=4)



    '''
    d =  helper.oauth.access_token(code='ef8c43d435edac03b83a12f58ee4779f')  
    print d
    with open('./token.txt', 'w') as f:
        f.write(str(d))

    printResult(ipc.files_put(token, '/token.txt', open('./access_token.txt')))
    result = ipc.files_put(access_token, '/analysis.mp4', open('./analysis.mp4', 'rb'))
    printResult(result)

    
    result =ipc.media(access_token, '/analysis.mp4')
    printResult(result)

    with open('./refresh_token.txt') as f:
        refresh_token = f.read()
    print refresh_token
    resp = my_oauth.access_token(grant_type='refresh_token', refresh_token=refresh_token.strip())
    print resp
    '''
