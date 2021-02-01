import os, subprocess, sys, grp
from HighThroughput.communication.mysql import mysql_query

def resubmit(qid = None, server = None, args = None):
    if qid == None:
        qid = sys.argv[1]

    if server == None:
        server = os.getenv('VSC_INSTITUTE_CLUSTER')

    script = mysql_query('SELECT `submit` FROM `queues` WHERE `id` = ' + str(qid))['submit']

    args = '' + sys.argv[2] + ' ' + sys.argv[3] + ' ' + sys.argv[4]
#    args = '' + sys.argv[2] + ' ' + str(2) + ' ' + sys.argv[4]
    if server != 'breniac':
        execute(script + ' ' + str(qid) + ' ' + str(args))
    else:
        print('ssh login1 "' + script + ' ' + str(qid) + ' ' + str(args) + '"')
        execute('ssh login1 "' + script + ' ' + str(qid) + ' ' + str(args) + '"')
    print('Submitted new calculation in queue ' + str(qid) + ' on server ' + server + '.')
    return True

def execute(command):
    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    out = out.decode();
    err = err.decode();
    print(out)
    print(err, file=sys.stderr)

    if err in locals():
        #raise Exception('Error in executing bash-command.')
        return False
    else:
        return out

def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False

def mkdir(command):
    if not os.path.isdir(command):
        stat_info = os.stat(os.getcwd())
        uid = stat_info.st_uid
        gid = stat_info.st_gid
        os.makedirs(command,0o774)
        os.chown(command,-1,gid)


def remove(command):
    if os.path.isfile(command):
        os.remove(command)
    else:
        print(str(command)+' is not a file.')

def error_catch(command):
    try:
        execute(command)
        return True
    except:
        return False

def getNodeInfo():
    from collections import Counter
    nodefile = subprocess.Popen('cat $PBS_NODEFILE',stdout=subprocess.PIPE,shell=True)
    nodefile = [x.split('.')[0].replace('node','') for x in filter(None,nodefile.communicate()[0].decode().split('\n'))]
    corecount = Counter()
    for node in nodefile:
        corecount[node] += 1
    return corecount

def getClass( kls ):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)            
    return m
