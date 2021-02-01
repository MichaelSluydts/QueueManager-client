from HighThroughput.communication.mysql import *
from HighThroughput.utils.generic import  *
from HighThroughput.io.Gaussian import *
import os,time,shutil,subprocess,linecache, threading
#cleanup function

def inherit(stat,qdir,cfile):
    if stat < 2:
        inputfile = os.path.join(qdir, 'import', str(cfile) + '.com')
    else:
        inputfile = os.path.join(qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(int(stat)-2), str(cfile) + '.com')
    shutil.copy(inputfile, './' + str(cfile) + '.com')

    return 0 

def abort(cinfo,delay=0,mode = 0):
    import HighThroughput.manage.calculation as manage
    # either switch between electronic and ionic or auto based on ibrion is possible
    #for now 0 is electronic stop, 1 ionic
    #time.sleep(delay)
    #open('aborted', 'a').close()
    #manage.restart(cinfo['id'])
    #psettings = manage.getSettings(manage.calcid)
    #if 'continue' in psettings.keys():
    #    psettings['continue'] = str(int(psettings['continue']) + 1)
    #else:
    #    psettings['continue'] = '1'
    #manage.modify({'settings' : psettings, 'id' : manage.calcid})
    return 0


def checkpointStart(cinfo,early=4400):
    walltime = int(os.getenv('PBS_WALLTIME'))
    thread = threading.Thread(target=abort,args=(cinfo,walltime-early,0))
    thread.daemon = True
    thread.start()
    return 0

def cont(calc,settings):
    import HighThroughput.manage.calculation as manage
    bakc = 0
    bakl = 0
    for file in os.listdir(os.curdir):
        if os.path.isfile(file) and file[6:10] == '.com':
            baks += 1
        if os.path.isfile(file) and file[6:10] == '.log':
            bako += 1

    if os.path.isfile(settings['name'] + '.com') and os.stat(settings['name'] + '.com').st_size > 0:
        shutil.copy(COMname,COMname + '.bak' + str(baks))
    #    if 'SCF=Restart' not in settings['route']:
     #       settings['route'] += ' SCF=Restart'

    if os.path.isfile(settings['name'] + '.log') and os.stat(settings['name'] + '.log').st_size > 0:
        os.rename(settings['name'] + '.log',settings['name'] + '.log' + '.bak' + str(bako))
    psettings = manage.getSettings(calc['parent'])
    if 'continued' not in psettings.keys():
        psettings['continued'] = 1
    else:
        psettings['continued'] += 1
    manage.updateSettings(psettings, calc['parent'])
    return calc

def finish():
    #end and readresults, readsettings too possibly, makecif populateresults and convert E/atom etc possibilities of using tables for chemical potentials
    #DOS and bandstructure options here too or in seperate postprocess func
    #Incorporate HTfinish, other httools should go somewhere too
    print('')
    return 0

def initialize(settings):
    #print 'write incar kpoints potcar, make directory?'
    #inherit()
    writeSettings(settings)
    return 0

def prepare(settings):
    #preparing any configs, can turn on SP and SO here too
    parallelSetup(settings)
    #print 'settings should be modified anyways'
    return settings

def detectSP(settings):
    if settings['multiplicity'] > 1:
        magnetic = True
    else:
        magnetic = False
    return magnetic

def detectSO(poscar):
    #we're doing organic chem here, let me know when needed
    return relativistic

def run(ratio = 1,cwd = None):
    #could move hybrid to parallel setup
    if cwd == None:
        cwd = os.getcwd();
    COMname = subprocess.Popen('ls -la | grep com | awk \'{print $9}\'',stdout=subprocess.PIPE,shell=True).communicate()    [0].strip()
    return execute('g09 < ' + COMname + ' > ' + COMname.strip('.com') + '.log')
    

def readSettings(settings):
    settings = readCOM()
    return settings

def parallelSetup(settings):
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    settings['ncore'] = ncore
    fmem = subprocess.Popen('free -m | fgrep cache: | awk \'{print $4}\'',stdout = subprocess.PIPE, shell=True).communicate()[0].strip()
    settings['mem'] = fmem + 'mb'
    return settings

def setupDir(settings):
    #print 'can make potcar and writesettings'
    #inherit too
    #Currently not implemented
    writeSettings(settings)
    return 0

def writeSettings(settings):
    writeCOM(settings)
    return 0
