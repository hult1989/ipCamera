import hashlib
import time
import json
import urllib2, urllib

device_token = 'Al_R8VsPSEqAYmxicJ-DSMM3nlCg3D9tNq8veR-CDMzO'
appkey = '56823bdce0f55adc18002599'
method = 'POST'
url= 'http://msg.umeng.com/api/send'
app_master_secret= 'o59ylkuhrmss0giesn2pnbkiwqetefzw'

def md5(s):
    m = hashlib.md5(s)
    return m.hexdigest()

def pushMsg(filenameDict):
    with open('./file_request.json') as f:
        request = f.read()
    request = eval(request)
    request['timestamp'] = str(int(time.time()))
    for filaname, fileurl in filenameDict.items():
        request['payload']['extra'].clear()
        request['payload']['extra'][filename] = fileurl
    timestamp = request['timestamp']
    post_body = json.dumps(request)
    sign = md5('%s%s%s%s' %(method, url, post_body, app_master_secret))

    path = url + '?sign=' + sign
    #pushRqst = urllib2.Request(path)
    try:
        resp = urllib2.urlopen(path, data=post_body).read()
        print resp
    except urllib2.HTTPError as e:
        print e.reason, e.read()
    except urllib2.URLError as e:
        print e.reason


if name == '__main__':
    pushMsg({'d.MP4': 'www.baidu.com'})
