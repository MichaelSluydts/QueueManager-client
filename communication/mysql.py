import http.client,urllib,json,os.path
from datetime import datetime
import ssl
import time
from functools import wraps

from http.client import HTTPException, NotConnected, ResponseNotReady, RemoteDisconnected


def retry(exceptions, tries=3, delay=30, backoff=2, logger=None):
    """
    Retry calling the decorated function using an exponential backoff.

    Args:
        exceptions: The exception to check. may be a tuple of
            exceptions to check.
        tries: Number of times to try (not retry) before giving up.
        delay: Initial delay between retries in seconds.
        backoff: Backoff multiplier (e.g. value of 2 will double the delay
            each retry).
        logger: Logger to use. If None, print.
    """
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = '{}, Retrying in {} seconds...'.format(e, mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


@retry((HTTPException, NotConnected, ResponseNotReady, RemoteDisconnected))
def mysql_query(query,blob=''):
    configfile= open(os.path.join(os.path.expanduser('~'),'.highthroughput'),'r')
    login = json.loads(configfile.read())
    context = ssl.create_default_context()
    context.load_verify_locations('/etc/pki/tls/cert.pem')
    conn = http.client.HTTPSConnection('HOSTNAME',context=context,timeout=900)
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    params = urllib.parse.urlencode({'query' : query.replace('<','%3C').replace('>','%3E'), 'blob' : blob, 'email' : login['email'], 'token' : login['token']}, quote_via=urllib.parse.quote_plus)
    params.encode('utf-8')
    conn.request('POST','APIPATH',params,headers)
    response = None
    response = conn.getresponse().read()
    try: 
        data = json.loads(response.decode())
        if len(data) == 1:
            data = data[0]
    except:
        data = response.decode()

    conn.close()
    return data

def mysql_query_profile(query,blob=''):
    startTime = datetime.now()
    print('\n\nstart')
    configfile= open(os.path.expanduser('~') + '/.highthroughput','r')
    login = json.loads(configfile.read())
    print('load config')
    print(datetime.now() - startTime)
    conn = http.client.HTTPConnection('HOSTNAME')
    print('connected')
    print(datetime.now() - startTime)
    headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}
    params = urllib.parse.urlencode({'query' : query, 'blob' : blob, 'email' : login['email'], 'token' : login['token']})
    print('encoded')
    print(datetime.now() - startTime)
    conn.request('POST','API_PATH',params,headers)
    print('posted')
    print(datetime.now() - startTime)
    response = conn.getresponse().read()
    print('read response')
    print(datetime.now() - startTime)
    try: 
        data = json.loads(response)
        if len(data) == 1:
            data = data[0]
    except:
        data = response
    print('json parsed')
    print(datetime.now() - startTime)
    print('\n\n')
    return data

owner = mysql_query('')
