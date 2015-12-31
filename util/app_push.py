import hashlib
import time
import json
import urllib2, urllib


def md5(s):
    m = hashlib.md5(s)
    return m.hexdigest()

with open('./file_request.json') as f:
    request = f.read()


request = eval(request)
request['timestamp'] = str(int(time.time()))
request['payload']['extra']['filename'] = 'some url'
appkey = '56823bdce0f55adc18002599'
app_master_secret= 'o59ylkuhrmss0giesn2pnbkiwqetefzw'
timestamp = request['timestamp']
method = 'POST'
device_token = 'Al_R8VsPSEqAYmxicJ-DSMM3nlCg3D9tNq8veR-CDMzO'
url= 'http://msg.umeng.com/api/send'
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

