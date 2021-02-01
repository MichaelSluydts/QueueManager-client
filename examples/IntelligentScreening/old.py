#!/usr/bin/env python
import shutil, os, sys, re
import subprocess
from subprocess import Popen, PIPE
from sys import argv

import ase.io

import HighThroughput.manage.calculation as HT
import HighThroughput.io

import json
import time
import random

from numpy.linalg import norm
from numpy import dot, arccos, degrees, floor, prod

#sleep = random.randrange(20)
#print('Random sleep... ZzZzZz for '+str(sleep)+' seconds, before starting script.')
#time.sleep(sleep)


qid = argv[1]
submit_arg = '' + argv[2] + ' ' + argv[3] + ' ' + argv[4]
print("Running on queue " + argv[1] + " with a walltime of " + argv[2] + "h, using " + argv[3] + " nodes and " + argv[4] + " cores.")

version = ''+argv[5]
#version = 1

if os.getenv('VSC_INSTITUTE_CLUSTER') == 'muk':
    qdir = os.path.join('/gpfs/scratch/projects/project_gpilot/vsc40479', 'queues', str(qid))
elif os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
    qdir = os.path.join('/scratch/leuven/404/vsc40479/queues',str(qid))
else:
    qdir = os.path.join('/user/scratch/gent/vsc404/vsc40479', 'queues', str(qid))
def execute(command):
    out, err = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()
    print(out)
    print >> sys.stderr, err

    if err in locals():
        #raise Exception('Error in executing bash-command.')
        return False
    else:
        return out

def mkdir(command):
    if not os.path.isdir(command):
        os.mkdir(command)

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


#os.chdir(qdir + '/fetchid')

#HT.fetchgetstart(qid)
cinfo = HT.fetchgetstart(qid)

#cid = HT.calcid
cid = cinfo['id']

#cinfo = HT.get(cid)
cfile = cinfo['file']
status = int(cinfo['stat'])

#cinfo['settings']['INCAR']['ENCUT'] = 300       #Only for fast debugging
#cinfo['settings']['KPOINTS']['K'] = "1 1 1"     #Only for fast debugging

#settings = json.loads(cinfo['settings'])
settings = HT.getSettings(cid)

INCAR_dict = settings['INCAR']
KPOINTS_dict = settings['KPOINTS']

print('Server: '+cinfo['server'])
if int(cinfo['queue']) == 237:
    KPOINTS_dict['K'] = "5 5 5"
elif int(cinfo['queue']) == 238:
    KPOINTS_dict['K'] = "5 5 5"
elif int(cinfo['queue']) == 239:
    KPOINTS_dict['K'] = "5 5 5"

KPOINTS_dict['mode'] = "G" #Voor hexagonale cellen: shift k-punt naar Gammapunt (G), andere cellen: Monkhorst (M)
INCAR_dict['ALGO'] = 'A'
INCAR_dict['ICHARG'] = 2
INCAR_dict['ENCUT'] = '520'
INCAR_dict['NCORE'] = 28
INCAR_dict['NPAR'] = 4
if int(status) < 17:
    INCAR_dict['ISIF'] = 4
    INCAR_dict['IBRION'] = 2
    INCAR_dict['NELM'] = 200
    INCAR_dict['NSW'] = 1000
    INCAR_dict['ICHARG'] = 1
    INCAR_dict['ISTART'] = 1
if int(status) < 15:
    INCAR_dict['ISMEAR'] = 1
    INCAR_dict['SIGMA'] = 0.05
else:
    INCAR_dict['NSW'] = 0
    INCAR_dict['IBRION'] = -1
    INCAR_dict['ISIF'] = 0
    INCAR_dict['NELM'] = 2000

settings = {'INCAR':INCAR_dict, 'KPOINTS':KPOINTS_dict}
#print('Updating settings (NPAR)')
#HT.updateSettings(settings, cid)
print(settings)
if os.path.isfile(qdir + '/CALCULATIONS/' + str(cfile) + '/STEP3/POSCAR'):
    crystal = ase.io.read(qdir + '/CALCULATIONS/' + str(cfile) + '/STEP3/POSCAR')
    cell = crystal.get_cell();
    a = cell[0];
    b = cell[1];
    c = cell[2];
    na = round(norm(a),3);
    nb = round(norm(b),3);
    nc = round(norm(c),3);
    nat = crystal.get_number_of_atoms()

    biglim = 20000./nat
    smallim = 2500./nat

    lc = [na,nb,nc]
    kp = [11,11,11]
    small = float(min(lc))
    for i in range(0,3):
        ratio = round(11.*small/lc[i],0)
        if ratio %2 == 0:
            ratio = ratio+1
            kp[i] = ratio
    kp = [int(x) for x in kp]
    while(prod(kp) < biglim):
        kp[0] += 2
        kp[1] += 2
        kp[2] += 2
    smallkp = [int(floor(float(x)/2.)) for x in kp]
    smallkp = [ x+ 1 if x %2 ==0 else x for x in smallkp]
    while(prod(smallkp) < smallim):
        smallkp[0] += 2
        smallkp[1] += 2
        smallkp[2] += 2


if status== 1:

    os.chdir(qdir+'/CALCULATIONS')
    mkdir(str(cfile))

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile))

    mkdir('./STEP3')
    os.chdir('./STEP3')

    shutil.copy('/scratch/leuven/404/vsc40479/queues/' + str(qid)  + '/import/' + str(cfile) + '.vasp', './POSCAR')
    #shutil.copy('/data/gent/vsc404/vsc40479/tier1/237/import/CHGCAR' + str(cfile), './CHGCAR')

    crystal = ase.io.read(qdir + '/CALCULATIONS/' + str(cfile) + '/STEP3/POSCAR')
    cell = crystal.get_cell();
    a = cell[0];
    b = cell[1];
    c = cell[2];
    na = round(norm(a),3);
    nb = round(norm(b),3);
    nc = round(norm(c),3);
    nat = crystal.get_number_of_atoms()

    biglim = 20000./nat
    smallim = 2500./nat

    lc = [na,nb,nc]
    kp = [11,11,11]
    small = float(min(lc))
    for i in range(0,3):
        ratio = round(11.*small/lc[i],0)
        if ratio %2 == 0:
            ratio = ratio+1
            kp[i] = ratio
    kp = [int(x) for x in kp]
    while(prod(kp) < biglim):
        kp[0] += 2
        kp[1] += 2
        kp[2] += 2

    smallkp = [int(floor(float(x)/2.)) for x in kp]
    smallkp = [ x+ 1 if x %2 ==0 else x for x in smallkp]
    while(prod(smallkp) < smallim):
        smallkp[0] += 2
        smallkp[1] += 2
        smallkp[2] += 2


    poscar = open('POSCAR','r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()
    count = len(re.findall("[a-zA-Z_]+", elements))
    execute('POTgen_MP ' + str(elements))

    poscar.close()

    print('STATUS 5 started')
    print('= STEP 3: EOS-prepare')

    step = 3

    atoms = ase.io.read('POSCAR',format="vasp")
    volume = float(atoms.get_volume())


    for i in xrange(94, 107, 2):
        I = 0.01*i

        os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))

        mkdir(str(I))
        shutil.copy('./POSCAR','./' + str(I) + '/POSCAR')
        shutil.copy('./POTCAR','./' + str(I) + '/POTCAR')
        #shutil.copy('./CHGCAR','./' + str(I) + '/CHGCAR')
        os.chdir('./' + str(I))
        KPOINTS_dict['K'] = str(smallkp[0]) + ' ' + str(smallkp[1]) + ' ' + str(smallkp[2])
        HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict, os.getcwd())
        HighThroughput.io.VASP.writeINCAR(INCAR_dict, os.getcwd())

        poscar = open('POSCAR','r')
        lines = poscar.readlines()
        lines[1] = ' -' + str(volume*I) + '\n'

        poscar = open('POSCAR','w')
        poscar.writelines(lines)
        poscar.close()

        os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))

    print('EOS 0.94')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step)+'/0.94')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/CHGCAR')

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/0.94/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/0.94/tempout vasp_std')

    execute('free -m; date')

    print('END STATUS 5 / STEP 3')

elif status==3:
    print('STEP 7 started')

    step = 3

    print('EOS 0.96')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step)+'/0.96')

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/0.96/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/0.96/tempout vasp_std')

    execute('free -m; date')

elif status==5:
    print('STEP 9 started')

    step = 3

    print('EOS 0.98')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step)+'/0.98')

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/0.98/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/0.98/tempout vasp_std')

    execute('free -m; date')

elif status==7:
    print('STEP 11 started')

    step = 3

    print('EOS 1.0')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step)+'/1.0')

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/1.0/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/1.0/tempout vasp_std')

    execute('free -m; date')

elif status==9:
    print('STEP 13 started')

    step = 3

    print('EOS 1.02')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step)+'/1.02')

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/1.02/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/1.02/tempout vasp_std')

    execute('free -m; date')

elif status==11:
    print('STEP 15 started')

    step = '3/1.04'

    print('EOS 1.04')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/tempout vasp_std')

    execute('free -m; date')

elif status==13:
    print('STEP 17 started')

    step = '3/1.06'

    print('EOS 1.06')

    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/tempout vasp_std')

    execute('free -m; date')

elif status==15:
    print('STEP 19 started')

    step = 4

    mkdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))
    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/STEP'+str(step))

    execute('STEP4_prepare')

    if execute('eos EOS_data 1 1')==False:
        print('Failed executing eos.')
        error = 'EOS-error'

    elif os.path.isfile('EOS_data.eosout'):
        volume = float(Popen('grep V0 EOS_data.eosout | awk \'{print $2}\' ', stdout=PIPE, shell=True).communicate()[0])
        best = ''
        diff = 999999999
        for e in os.listdir('../STEP3/'):
            if os.path.isdir(os.path.join('../STEP3',e)):
                vol = float(Popen('grep \'volume \'  ../STEP3/' + e + '/OUTCAR | tail -n 1 | awk \'{print $5}\'', stdout=PIPE, shell=True).communicate()[0])
                if abs(vol - volume) < diff:
                    diff = abs(vol - volume)
                    best = e

        shutil.copy('../STEP3/'+ best + '/CONTCAR','./POSCAR')
        shutil.copy('../STEP3/' + best + '/POTCAR','./POTCAR')
        if os.path.isfile('../STEP3/' + best + '/CHGCAR'):
            shutil.copy('../STEP3/' + best + '/CHGCAR','./CHGCAR')
        INCAR_dict['IBRION'] ="-1"
        INCAR_dict['ISIF'] = "0"
        INCAR_dict['NSW'] = "0"
        KPOINTS_dict['K'] = str(kp[0]) + ' ' + str(kp[1]) + ' ' + str(kp[2])

        HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict, os.getcwd())
        HighThroughput.io.VASP.writeINCAR(INCAR_dict, os.getcwd())

        poscar = open('POSCAR','r')
        lines = poscar.readlines()
        lines[1] = ' -' + str(volume) + '\n'

        poscar = open('POSCAR','w')
        poscar.writelines(lines)
        poscar.close()

        execute('free -m; date; touch WAVECAR')
        remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/STEP' +str(step)+ '/tempout')

        execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/STEP'+str(step)+'/tempout vasp_std')

        execute('free -m; date')
    else:
        print( 'Something wrong while EOS-fitting. Error...')
        error = 'EOS-error'

elif status==17:
    print('STEP 21 started')

    step = 'DOS'

    mkdir(qdir+'/CALCULATIONS/'+str(cfile)+'/'+str(step))
    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/'+str(step))

    shutil.copy('../STEP4/CONTCAR', './POSCAR')
    shutil.copy('../STEP4/POTCAR', './POTCAR')
    shutil.copy('../STEP4/CHGCAR', './CHGCAR')
    KPOINTS_dict['K'] = str(kp[0]) + ' ' + str(kp[1])+ ' ' + str(kp[2])

    HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict, os.getcwd())
    HighThroughput.io.VASP.writeINCAR(INCAR_dict, os.getcwd())

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/' +str(step)+ '/tempout')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/'+str(step)+'/tempout vasp_std')

    execute('free -m; date')

elif status==19:
    print('STEP 23 started')

    step = 'BANDS'

    mkdir(qdir+'/CALCULATIONS/'+str(cfile)+'/'+str(step))
    os.chdir(qdir+'/CALCULATIONS/'+str(cfile)+'/'+str(step))

    shutil.copy('../STEP4/CONTCAR', './POSCAR')
    shutil.copy('../STEP4/POTCAR', './POTCAR')
    shutil.copy('../STEP4/CHGCAR', './CHGCAR')
    HighThroughput.io.VASP.writeKPOINTS(KPOINTS_dict, os.getcwd())
    HighThroughput.io.VASP.writeINCAR(INCAR_dict, os.getcwd())

    execute('free -m; date; touch WAVECAR')
    remove(''+ qdir+'/CALCULATIONS/' + str(cfile) + '/' +str(step)+ '/tempout')

    execute('aconvasp --kpath  < POSCAR > KPOINTS')

    shutil.copy('KPOINTS', 'KPOINTStemp')
    os.remove('KPOINTS')

    KPOINTSstarted = True
    KPOINTSfile = open('KPOINTStemp','r')
    for line in KPOINTSfile:
        if KPOINTSstarted and line[:1]!='/':
            if "G-M-K-G-A-L-H-A L-M K-H" in line:
                line = line.replace("G-M-K-G-A-L-H-A L-M K-H","G-M-K-G-A-L-H-A|L-M|K-H")
            KPOINTS = open('KPOINTS','a')
            KPOINTS.write(line)
            KPOINTS.close()
        if line[:1]=='/':
            KPOINTSstarted =  not KPOINTSstarted
    os.remove('KPOINTStemp')

    execute('mympirun --output ' +qdir+'/CALCULATIONS/' + str(cfile) + '/'+str(step)+'/tempout vasp_std')

    execute('free -m; date')

else:
    print('Status ' + str(status) + ' is not a valid status. Calculation terminated.')
    sys.exit()


#UPDATE POTCAR INFO

POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
settings['POTCAR'] = POTCAR_version.strip().replace('\n',', ')

#END CALCULATION AND FETCH RESULTS

energy = execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\'')

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
    print('This is the HT.end cid: ' + str(cid))

    ended = 0
    tries = 0
    while(ended == 0 and tries < 10):
        ended = HT.end(cid)
        tries = tries + 1
        print tries
        time.sleep(random.randint(10,100))
    if(ended == 0):
        print('ERROR: I tried to end calculation ' + str(cid) + str(tries) + ' times, but no succes.') #tries should always be 10
        HT.updateResults({'error':'Ending calculation failed'}, cid)

    else:
        if status<15:
            #os.remove('CHGCAR')
            os.remove('CHG')

        results = HT.getResults(cid)

        #could leave this out when working with QZP's

        poscar = open('POSCAR','r')
        lines = poscar.readlines()

        numberofatoms = lines[6][:-1].lstrip()
        numberofatoms = " ".join(numberofatoms.split())
        numberofatoms = sum(map(int, numberofatoms.split(' ')))

        energy = float(energy)

        Eatom = energy/numberofatoms
        results['Eatom'] = Eatom

        atoms = lines[5].split()

        energies = {'Te':-3.142188083,'K':-1.04693431,'Tl':-2.2266554,'Se':-3.498123137,'Rb':-0.936014755,'Sb':-4.13566371,'P':-5.373717185,'Bi':-3.885356122,'Po':-3.07473254,'Al':-3.745478105,'Ca':-1.929739603,'In':-2.55987617,'Sn':-3.846317905,'Ga':-2.905926696,'Mg':-1.506391565,'Na':-1.311801313,'Ba':-1.90827009,'Sr':-1.636048335,'Cs':-0.852268485,'S':-4.125889916,'Si':-5.424861565,'Ge':-4.51831862,'Pb':-3.565225973,'As':-4.66985772,'Li':-1.910459733}


        if len(atoms)==1:
            results['Eformation'] = Eatom  - float(energies[str(atoms[0])])
        elif len(atoms)==4:
            results['Eformation'] = Eatom  - float(6*energies[str(atoms[0])] + energies[str(atoms[1])] + 4*energies[str(atoms[2])] + 3*energies[str(atoms[3])])/14

        results['volume'] = float(Popen('grep volume OUTCAR | tail -1 | awk \'{print $5}\' ', stdout=PIPE, shell=True).communicate()[0])

        crystal = ase.io.read('CONTCAR')
        cell = crystal.get_cell()

        a = cell[0];
        b = cell[1];
        c = cell[2];
        na = round(norm(a),3);
        nb = round(norm(b),3);
        nc = round(norm(c),3);

        results['a'] = na
        results['b'] = nb
        results['c'] = nc
        results['alpha'] = round(degrees(arccos(dot(b,c)/nb/nc)),1)
        results['beta'] = round(degrees(arccos(dot(c,a)/nc/na)),1)
        results['gamma'] = round(degrees(arccos(dot(a,b)/na/nb)),1)

        print('Updating results')
        print results
        HT.updateResults(results, cid)

print('Updating settings')
print settings
HT.updateSettings(settings, cid)


#RELOOP to the script

#exit() #No new calculations allowed.

cid_new = HT.fetch(qid)

print('Fetched calculation '+str(cid_new)+' from queue '+str(qid)+'.')

os.chdir(qdir+'/LOGFILES')

if int(cid_new) > 0:
    print('Queue not empty: submit new job.')
    execute(' ssh login1 "~/bin/HTtools/QZPsubmit_reeosleuven ' + str(qid) + ' ' + str(argv[2]) + ' ' + str(argv[3]) + ' ' + str(argv[4]) + '"')
else:
    print('No calculations left; end script without submitting new job.')
    execute('touch '+str(qid)+'_'+str(cid)+'_fetch0')

execute('qstat')
