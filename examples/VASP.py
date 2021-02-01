#!/usr/bin/env python
import os, random, re, shutil, subprocess, sys, time

import HighThroughput.manage.calculation as HT
import HighThroughput.manage.template as template
import HighThroughput.io
from HighThroughput.utils.generic import *
from HighThroughput.modules.VASP import *

qid = sys.argv[1]
submit_arg = '' + sys.argv[2] + ' ' + sys.argv[3] + ' ' + sys.argv[4]

qdir = os.path.join(os.getenv('VSC_SCRATCH'), '/queues/', str(qid))
os.chdir(os.path.join(qdir, '/fetchid'))

start = 0
counter = 0

#Fetching jobs, ensuring we don't still somehow run the same job twice
print('Fetching...')
cinfo = HT.fetchgetstart(qid)
print('Fetched ' + str(cid))
cfile = cinfo['file']
status = cinfo['stat']

if int(cid) <= 0:
    print('No calculations left')
    #This is the logfile directory (PBS and own logs)
    os.chdir(os.path.join(qdir,'/LOGFILES'))
    #Make a file showing the queue no longer has any feasible jobs left, imperfect, new jobs may be added when others finish
    execute('touch ' + str(qid) + '_fetch0')
    sys.exit()

#Real script starts here

cid = cinfo['id']

cfile = cinfo['file']
status = int(cinfo['stat'])
inputfile = os.path.join(qdir, '/import/', str(cfile) + '.vasp')

print('THE STAT is' + str(status))

#temp variable for INCAR for manual mods
INCAR = cinfo['settings']['INCAR']

if int(qid) in [149,150,155,156]:
    INCAR['ENCUT'] = 600

if detectSP(inputfile):
    INCAR['ISPIN'] = 2

print('Server: ' + cinfo['server'])

#Setup default 1 point per node etc

print cinfo['settings']

parallelSetup(cinfo['settings'])

print cinfo['settings']

INCAR['KPAR'] = str(sys.argv[3])

cinfo['settings']['INCAR'] = INCAR

if status== 1:
    print('STEP 1 started')
    step = 1

    os.chdir(qdir+'/CALCULATIONS')
    mkdir(str(cfile))

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile))

    mkdir('./STEP1')
    os.chdir('./STEP1')

    shutil.copy(qdir + '/import/' + str(cfile) + '.vasp', './POSCAR')
    poscar = open('POSCAR','r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()


    HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict, os.getcwd())
    HighThroughput.io.VASP.writeINCAR(INCAR_dict, os.getcwd())

    execute('POTgen ' + str(elements))

    poscar.close()

    execute('free -m; date; touch CHGCAR WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/tempout')



    print('END STATUS 1 / STEP 1')

elif status==3:
    print('STEP 3 started')

    step = 2

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile))
    if os.path.isdir('./STEP'+str(step)):
        os.rmdir('./STEP'+str(step))
    mkdir('./STEP'+str(step))
    os.chdir('./STEP'+str(step))

    shutil.copy('../STEP'+str(step-1)+'/CONTCAR', './POSCAR')
    shutil.copy('../STEP'+str(step-1)+'/POTCAR', './POTCAR')
    shutil.copy('../STEP'+str(step-1)+'/CHGCAR', './CHGCAR')
    #shutil.copy('../STEP'+str(step-1)+'/WAVECAR', './WAVECAR')


    settings = {'INCAR':INCAR_dict, 'KPOINTS':KPOINTS_dict}

    HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict)
    HighThroughput.io.VASP.writeINCAR(INCAR_dict)

    execute('free -m; date; touch CHGCAR WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/tempout vasp')

    execute('free -m; date')

    print('END STATUS 3 / STEP 2')

else:
    print('Not a valid status. Calculation terminated.')
    sys.exit()


#UPDATE POTCAR INFO

POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
settings['POTCAR'] = POTCAR_version.strip().replace('\n',', ')

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

    if status<19:
        os.remove('CHG')

    results = HT.getResults(cid)

    #could leave this out when working with QZP's

    numberofatoms = lines[6][:-1].lstrip()
    numberofatoms = " ".join(numberofatoms.split())
    numberofatoms = sum(map(int, numberofatoms.split(' ')))

    energy = float(energy)

    if step == 1:
        results['E0PBE'] = energy
    else:
        results['E0HSE06'] = energy
        results['E0PBE'] = float(execute('grep \'energy  without entropy\'  ../STEP1/OUTCAR | tail -1 | awk \'{ print $4 }\''))



    print('Updating results')
    print results
# updateresults could be assumed from dictionary keys and automated.
    HT.updateResults(results, cid)

print('Updating settings')
print settings
HT.updateSettings(settings, cid)


#RELOOP to the script

cid_new = HT.fetch(qid)

print('Fetched calculation '+str(cid_new)+' from queue '+str(qid)+'.')

os.chdir(qdir+'/LOGFILES')

if int(cid_new) > 0:
#    print('Script ONCE: do not submit new job')
    #execute('vaspsubmit ' + str(qid) + ' ' + str(submit_arg))
else:
    print('No calculations left; end script without submitting new job.')
    execute('touch '+str(qid)+'_'+str(cid)+'_fetch0')

execute('qstat')

