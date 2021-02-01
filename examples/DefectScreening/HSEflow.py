#!/usr/bin/env python
import os, random, re, shutil, subprocess, sys, time,math

import HighThroughput.manage.calculation as HT
import HighThroughput.manage.template as template
from HighThroughput.io.VASP import *
from HighThroughput.utils.generic import *
from HighThroughput.modules.VASP import *
from HighThroughput.errors.generic import *
qid = sys.argv[1]
submit_arg = '' + sys.argv[2] + ' ' + sys.argv[3] + ' ' + sys.argv[4]

if (int(qid) == 160 or int(qid) == 159 or int(qid) == 158 or int(qid) < 156 or int(qid) > 160) and os.getenv('VSC_INSTITUTE_CLUSTER') == 'muk':
    qdir = os.path.join('/gpfs/scratch/projects/project_gpilot/vsc40479', 'queues', str(qid))
elif os.getenv('VSC_INSTITUTE_CLUSTER') == 'muk':
    qdir = os.path.join('/gpfs/scratch/users/vsc404/vsc40479', 'queues', str(qid))
else:
    qdir = os.path.join('/user/scratch/gent/vsc404/vsc40479', 'queues', str(qid))
#os.chdir(os.path.join(qdir, '/fetchid'))


#Fetching jobs, ensuring we don't still somehow run the same job twice
print('Fetching...')
cinfo = HT.fetchgetstart(qid)
print('Fetched ' + str(cinfo['id']))

if int(cinfo['id']) <= 0:
    print('No calculations left')
    #This is the logfile directory (PBS and own logs)
    os.chdir(os.path.join(qdir,'/LOGFILES'))
    #Make a file showing the queue no longer has any feasible jobs left, imperfect, new jobs may be added when others finish
  #  execute('touch ' + str(qid) + '_fetch0')
    sys.exit()

#Real script starts here

cfile = cinfo['file']
cid = cinfo['id']
cinfo['settings'] = json.loads(cinfo['settings'])
#cinfo['settings']['INCAR']['ENCUT'] = 1000
#cinfo['settings']['KPOINTS']['K'] = "30 30 30"
status = int(cinfo['stat'])

print('THE STAT is' + str(status))

print('Server: ' + cinfo['server'])


os.chdir(qdir+'/CALCULATIONS/')
mkdir(str(cfile))

os.chdir(qdir+'/CALCULATIONS/'+str(cfile))
step = int(math.ceil(float(cinfo['stat'])/2))
print('step' + str(step))
mkdir('./STEP' + str(step))
os.chdir('./STEP' + str(step))

if os.path.isfile('aborted'):
    os.remove('aborted')

if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

checkpointStart(cinfo,10000)

parent = HT.getSettings(cinfo['parent'])

if 'continue' not in parent.keys():
    parent['continue'] = 0
if 'continued' not in parent.keys():
    parent['continued'] = 0

if int(parent['continue']) > int(parent['continued']):
    print('Continuing job')
    cont(cinfo)
else:
    inherit(status,qdir,cfile)
    initialize(cinfo['settings'])

if detectSP('POSCAR'):
    cinfo['settings']['INCAR']['ISPIN'] = 2

if int(qid) in [150,156,171]:
    cinfo['settings']['INCAR']['ENCUT'] = 600
    cinfo['settings']['INCAR']['NELM'] = 60
    #cinfo['settings']['INCAR']['ISPIN'] = 1
if int(qid) != 171 and int(qid) != 156:
    cinfo['settings']['INCAR']['TIME'] = 0.1
    cinfo['settings']['INCAR']['NELM'] = 60


if int(qid) < 155:
    cinfo['settings']['KPOINTS']['K'] = '6 6 6'
    cinfo['settings']['INCAR']['NKRED'] = '6'
    cinfo['settings']['INCAR']['NELM'] = 120
else:
    cinfo['settings']['KPOINTS']['K'] = '4 4 4'
    cinfo['settings']['INCAR']['NKRED'] = '4'

if int(qid) == 167 or int(qid) == 171:
    cinfo['settings']['KPOINTS']['K'] = '12 12 12'
    cinfo['settings']['INCAR']['NKRED'] = '2'
cinfo['settings']['INCAR']['LSUBROT'] = '.TRUE.'
if int(cfile) == 10025486:
    cinfo['settings']['INCAR']['ALGO'] = 'A'
    cinfo['settings']['INCAR']['NELM'] = 30
    cinfo['settings']['INCAR']['TIME'] = 1.95
if int(cfile) == 10031153:
    cinfo['settings']['INCAR']['MAGMOM'] = '2*1.0000 2*-1.0000'

if int(cfile) == 10031210:
    cinfo['settings']['INCAR']['MAGMOM'] = '1. 1. -1. -1.'

parallelSetup(cinfo['settings'])
if os.getenv('VSC_INSTITUTE_CLUSTER') == 'muk':
    cinfo['settings']['INCAR']['NCORE'] = '16'
perror = HT.getResults(cinfo['parent'])
if perror.get('errors') != None:
    fixerrors(cinfo)
writeSettings(cinfo['settings'])
run()
finderrors(cinfo)
if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')



print('END STATUS ' + cinfo['stat'])


#UPDATE POTCAR INFO

POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
cinfo['settings']['POTCAR'] = POTCAR_version.strip().replace('\n',', ')

if os.path.isfile('aborted'):
    print('Calculation aborted')
    execute('betaHSE ' + str(qid) + ' ' + str(submit_arg))
    sys.exit()
#END CALCULATION AND FETCH RESULTS

energy = execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $4 }\'')

if 'error' in locals():
    HT.updateResults({'error':error}, cid)
elif energy=='' or not 'energy' in locals():
    HT.updateResults({'error':'Energy missing'}, cid)
    print('Energy missing! Error...')
elif not os.path.isfile('CHGCAR') and not os.path.isfile('CHG'):
    HT.updateResults({'error':'CHGCAR and CHG missing. VASP Error?'}, cid)
    print('CHGCAR/CHG missing. VASP Error?')
else:
    print('Energy OK. Ending calculation, deleting junk files and fetching results.')
    HT.end(cid)
        #cleanup function
    os.remove('CHG')

    results = json.loads(cinfo['results'])
    #could leave this out when working with QZP's

    energy = float(energy)

    if status == 1:
        results['E0PBE'] = energy
    else:
        results['E0HSE06'] = energy
        results['E0PBE'] = float(execute('grep \'energy  without entropy\'  ../STEP1/OUTCAR | tail -1 | awk \'{ print $4 }\''))

    print('Updating results')
# updateresults could be assumed from dictionary keys and automated.
    HT.updateResults(results, cid)

print('Updating settings')
HT.updateSettings(cinfo['settings'], cid)
newcalc = int(HT.fetch(str(qid)))
print(str(newcalc))
if int(HT.fetch(str(qid))) > 0 and int(qid) != 167 and int(qid) != 171:
    execute('betaHSE ' + str(qid) + ' ' + str(submit_arg))
# -*- coding: utf-8 -*-

