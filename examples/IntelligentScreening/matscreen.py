# -*- coding: utf-8 -*-
#!/usr/bin/env python

import os, random, re, shutil, subprocess, sys, time, json
import numpy as np
import HighThroughput.manage.calculation as HT
import HighThroughput.manage.template as template
from HighThroughput.io.VASP import *
from HighThroughput.utils.generic import mkdir, execute, resubmit
from HighThroughput.modules.VASP import *
from HighThroughput.errors.generic import *
#from HighThroughput.ML.models.priority import updateMLpriority

qid = sys.argv[1]
#Can change number of nodes based on step and kpoints too of course for the next submit
submit_arg = '' + sys.argv[2] + ' ' + sys.argv[3] + ' ' + sys.argv[4]

# Set up the queue directory paths, this is always the same and should be moved to the .highthroughput file in a dictionary except for manual overrides
user = os.getenv('USER')
scratch = os.getenv('VSC_SCRATCH_VO')
qdir = os.path.join(scratch, 'queues', str(qid))
submitscript = os.path.join(qdir,'matscreen') #this is what needs updating for auto error fix resubmit

# Fetching a job and immediately starting it, ensuring we don't run the same job twice
print('Fetching...')
cinfo = HT.fetchgetstart(qid)
print('Fetched calculation ' + str(cinfo['id']))

if int(cinfo['id']) <= 0:
    print('No calculations left')
    sys.exit()
    
#Defining directories
cdir = [os.path.join(qdir,'CALCULATIONS',cinfo['file'],x) for x in ['CALIB/low','RELAX/vol','RELAX/all','EOSL/1.0','EOSL/1.02','EOSL/0.98','EOSL/1.04','EOSL/0.96','EOSL/1.06','EOSL/0.94','RELAX/internalL','CALIB/high','EOSH/1.0','EOSH/1.02','EOSH/0.98','EOSH/1.04','EOSH/0.96','EOSH/1.06','EOSH/0.94','RELAX/internalH','ENERGY','DOS','BANDS']]
cdir = [os.path.join(qdir,'import')] + cdir

# Starting the actual calculations
status = int(cinfo['stat'])

print('Starting calculation ' + str(cinfo['id']) + ' on cluster: ' + cinfo['server'] + '.')

# Navigating to the directory of the current workflow step
os.chdir(os.path.join(qdir,'CALCULATIONS'))
mkdir(str(cinfo['file']))

os.chdir(os.path.join(qdir,'CALCULATIONS',cinfo['file']))
step = int(np.ceil(float(cinfo['stat'])/2))

# Configure settings per step
# By default always inherit
inheritcontcar = True
inheritchgcar = True
inheritwavecar = True
# Can define this by default, though I've added an if statement for each step anyways
inheritstep = step - 1
parent = HT.get(cinfo['parent'])
inheritmod = None
inheritgrid = False
rescale = 1.0

if parent['parent'] != '0':
    pparent = HT.getResults(parent['parent'])
    inheritmod = pparent.get('settingsmod')
    print('The following settingsmod will be inherited: ')
    print(inheritmod)

        
#==============================================================================
# In this section you can also make manual changes to the settings, for example:
# if int(qid) == 167 or int(qid) == 171:
#     cinfo['settings']['KPOINTS']['K'] = '12 12 12'
#     cinfo['settings']['INCAR']['NKRED'] = '2'
# cinfo['settings']['INCAR']['LSUBROT'] = '.TRUE.'
# if int(cfile) == 10025486:
#     cinfo['settings']['INCAR']['ALGO'] = 'A'
#     cinfo['settings']['INCAR']['NELM'] = 30
#     cinfo['settings']['INCAR']['TIME'] = 1.95
# if int(cfile) == 10031153:
#     cinfo['settings']['INCAR']['MAGMOM'] = '2*1.0000 2*-1.0000'
#==============================================================================

minkp = 2500

if step > 11:
    minkp = 10000

cinfo['settings']['INCAR']['ISMEAR'] = 0

if step > 1:
    eoscriteria1 = {'res' : 0.03, 'B0' : (3.,100.), 'BP' : None, 'V0' : (parent['results']['volume']*0.985/1.06,parent['results']['volume']*1.015/1.06), 'dirs' : cdir}
    eoscriteria2 = {'res' : 0.03, 'B0' : (3.,100.), 'BP' : None, 'V0' : (parent['results']['volume']*0.98/1.06,parent['results']['volume']*1.02/1.06), 'dirs' : cdir}

if step > 10:
    cinfo['settings']['INCAR']['ISPIN'] = 2

if step == 1:
    # Low Calibration
    minkp = 0
    inheritstep = 0
elif step == 2:
    # Vol relax
    inheritstep = 1
    # Modify the template
    cinfo['settings']['INCAR']['ISIF'] = 7
elif step == 3:
    # Full relax
    inheritstep = 2
    cinfo['settings']['INCAR']['ISIF'] = 3
elif step == 4:
    # EOS 1.0
    inheritstep = 3
    rescale = 1.0
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 5:
    # EOS 1.02
    inheritstep = 4
    inheritgrid = True
    rescale = 1.02
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 6:
    # EOS 0.98
    inheritstep = 4
    inheritgrid = True
    rescale = 0.98
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 7:
    # EOS 1.04
    inheritstep = 5
    inheritgrid = True
    rescale = 1.04/1.02
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 8:
    # EOS 0.96
    inheritstep = 6
    inheritgrid = True
    rescale = 0.96/0.98
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 9:
    # EOS 1.06
    inheritstep = 7
    inheritgrid = True
    rescale = 1.06/1.04
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 10:
    # EOS 0.94
    inheritstep = 8
    inheritgrid = True
    rescale = 0.94/0.96
    cinfo['results']['eos'] = ""
    cinfo['results']['eoscheck'] = eoscriteria1
    cinfo['settings']['INCAR']['ISIF'] = 4
elif step == 11:
    # Final internal relaxation
    cinfo['settings']['INCAR']['ISIF'] = 4
    #lorbit then max magnetic moment
    cinfo['results']['spincheck'] = 0.1
    rescale = -parent['results']['eos']['V0']
    inheritstep = 4
elif step == 12:
    # High calib
    minkp = 0
    inheritstep = 11
    rescale = 1.0
elif step == 13:
    # EOS 1.0
    #TO DO CHANGE STEP
    inheritstep = 12
    #rescale = 1.0
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 14:
    # EOS 1.02
    inheritstep = 5
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*1.02
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 15:
    # EOS 0.98
    inheritstep = 6
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*0.98/1.02
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
    cinfo['settings']['INCAR']['ENCUT'] = 520
elif step == 16:
    # EOS 1.04
    inheritstep = 7
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*1.04/0.98
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 17:
    # EOS 0.96
    inheritstep = 8
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*0.96/1.04
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 18:
    # EOS 1.06
    inheritstep = 9
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*1.06/0.96
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 19:
    # EOS 0.94
    inheritstep = 10
    inheritchgcar = False
    inheritwavecar = False
    #rescale = -parent['results']['volume']*0.94/1.06
    cinfo['results']['eos'] = ""
    cinfo['results']['eoscheck'] = eoscriteria2
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['IBRION'] = -1
    cinfo['settings']['INCAR']['ISIF'] = 2
elif step == 20:
    # Final internal relaxation
    cinfo['settings']['INCAR']['ISIF'] = 4
    rescale = -parent['results']['eos']['V0']
    inheritstep = 12
elif step == 21:
    # Final single point energy calculation
    cinfo['settings']['INCAR']['NSW'] = 1
    cinfo['settings']['INCAR']['ISMEAR'] = -5
    # For stress tensor
    cinfo['settings']['INCAR']['ISIF'] = 2
    inheritstep = 20
#elif step == 22:
    # DOS
#    inheritstep = 21
#    cinfo['settings']['INCAR']['ENCUT'] = 520
#elif step == 23:
    # BANDS
#    inheritstep = 22
#    cinfo['settings']['INCAR']['ENCUT'] = 520
#cleaning up certain chgcar and wavecars in later steps might be good
 
print('Starting step ' + str(step) + ' in ' + cdir[step] + '.')
mkdir(cdir[step])
os.chdir(cdir[step])

# Clearing
if os.path.isfile('aborted'):
    os.remove('aborted')

if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

# Start checkpointing, second argument should be how much time you need to write
# out the files necessary for restart, i. e. how much time before the walltime a 
# stop signal will be sent to your ab initio program.

# Could be automated based on LOOP time
checkpointStart(cinfo,1800)

# Here we continue the job if it was checkpointed in a previous job

if 'continue' not in parent['settings'].keys():
    parent['settings']['continue'] = 0
if 'continued' not in  parent['settings'].keys():
    parent['settings']['continued'] = 0

perror = parent['results']
if perror.get('errors') != None:
    fixerrors(cinfo)

if int( parent['settings']['continue']) > int(parent['settings']['continued']):
    print('Continuing job from calculation id: ' + str(cinfo['parent']) + '.')
    cont(cinfo)
else:
    print('Initializing job.')
    inherit(cinfo,cdir[inheritstep],contcar = inheritcontcar,chgcar = inheritchgcar,wavecar = inheritwavecar, grid = inheritgrid, settingsmod = inheritmod,rescale = rescale)
    #Verify your potcardir, potgen should possibly just become a python function.
    initialize(cinfo['settings'])

#Post setup modifications.
encutlow = 1.25*float(execute('grep ENMAX POTCAR | awk \'{print $3}\' | cut -d\; -f1 | sort -n | tail -n1'))

if step < 12:
    cinfo['settings']['INCAR']['ENCUT'] = encutlow
else:
    cinfo['settings']['INCAR']['ENCUT'] = 520

if detectSP('POSCAR'):
    # This could be abstracted further, though the magnetic elements chosen in 
    # detectSP are not uniquely chosen either.
    cinfo['settings']['INCAR']['ISPIN'] = 2

#Redivide KP AFTER initializing for settingsmod
setupKP(cinfo['settings'], minkp)
#Setup parallellization settings
parallelSetup(cinfo['settings'])

writeSettings(cinfo['settings'])

#Preprocessing
# can check eos errors based on e-v.dat
decompress()
run()
compress()

# Error catching

finderrors(cinfo)

# Checkpoint cleanup
if os.path.isfile('STOPCAR'):
    os.remove('STOPCAR')

print('Ending Calculation')

# Checkpoint abortion
if os.path.isfile('aborted'):
    print('Calculation aborted')
    resubmit()
    sys.exit()



# Post-processing (run hooks? or extra functions in VASP module)

# Gather results and settings and end calculation

# Nowadays I take the energy with sigma -> 0, while in theory without entropy should be nearly the same, 
# this seems more robust and is also used by the VASP group

# Store detected errors
if 'error' in locals():
    HT.updateResults({'error':error}, cinfo['id'])
else:
    print('Gathering results')
    results = gather(cinfo['results'])

    print('Updating results.')
# updateresults could be assumed from dictionary keys and automated.
    HT.updateResults(results, cinfo['id'])
    
        
    print('Energy OK. Ending calculation, deleting junk files and fetching results.')
    HT.end(cinfo['id'])
        #cleanup function
    # Can change this to a step dictionary
    os.remove('CHG')
    
print('Updating settings.')

# Update POTCAR INFO

POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
cinfo['settings']['POTCAR'] = POTCAR_version.strip().replace('\n',', ')

HT.updateSettings(cinfo['settings'], cinfo['id'])

# Update priority with Machine Learning model
#if step == 21:
#    updateMLPriority(cinfo['queue'], 42)

stat_info = os.stat(qdir)
uid = stat_info.st_uid
gid = stat_info.st_gid

for root, dirs, files in os.walk(os.path.join(qdir,'CALCULATIONS',cinfo['file'])):
    for momo in dirs:
        try:
            os.chown(os.path.join(root, momo), -1, gid)
            os.chmod(os.path.join(root, momo),0o774)
        except PermissionError as e:
            continue

    for momo in files:
        try:
            os.chown(os.path.join(root, momo), -1, gid)
            os.chmod(os.path.join(root, momo), 0o664)
        except PermissionError as e:
            continue

for root,dirs, files in os.walk(os.path.join(os.path.join(qdir,'LOGFILES'))):
    for momo in files:
        try:
            os.chown(os.path.join(root, momo), -1, gid)
            os.chmod(os.path.join(root, momo), 0o664)
        except PermissionError as e:
            continue


newcalc = int(HT.fetch(str(qid)))

if newcalc > 0:
    resubmit()
    print('Submitted new calculation in queue ' + str(qid) + '.')
else:
    print('Queue ' + str(qid) + ' is finished.')
print('Calculation ended.')
