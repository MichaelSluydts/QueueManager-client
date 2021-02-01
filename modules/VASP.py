from HighThroughput.utils.generic import  mkdir, execute, getNodeInfo, isfloat,resubmit
from HighThroughput.utils.eos import EquationOfState
from HighThroughput.io.VASP import rescalePOSCAR, writeINCAR, writeKPOINTS, readINCAR, readKPOINTS
import os, time, shutil, subprocess, threading, sys, ase.io,json
from HighThroughput.config import vasp
import HighThroughput.manage.calculation as manage
from HighThroughput.communication.mysql import mysql_query
from numpy.linalg import norm
import numpy as np
from pymatgen.io.vasp.outputs import Vasprun
import HighThroughput.manage.calculation as manage
from retry import retry

import warnings
warnings.filterwarnings("ignore")
import pymatgen
from pymatgen.ext.matproj import MPRester
from pymatgen import Composition
from pymatgen.entries.computed_entries import ComputedEntry
from pymatgen.core.units import FloatWithUnit
from pymatgen.analysis.reaction_calculator import ComputedReaction
from pymatgen.apps.borg.hive import VaspToComputedEntryDrone
from pymatgen.apps.borg.queen import BorgQueen
from pymatgen.analysis.phase_diagram import *
from pymatgen.entries.compatibility import MaterialsProjectCompatibility

#cleanup function

def inherit(calc,path,contcar=True,chgcar=True,wavecar=True,settingsmod=None,grid=False,rescale=1.0):
    #pstep = int(math.ceil(float(stat)/2.)) -1
    if path is None:
        return True
        #inputfile = os.path.join(qdir, 'import', str(cfile) + '.vasp')
    
        #qdir, 'CALCULATIONS/' + cfile + '/STEP' + str(pstep)
    if contcar:
        contcarnames = ['CONTCAR','POSCAR' + calc['file'] + '.vasp','POSCAR' + calc['file'], calc['file'], calc['file'] + '.vasp']
        for name in contcarnames:    
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                inputfile = temp
                print('Inheriting geometry from ' + inputfile + '.')
                shutil.copy(inputfile, './POSCAR')
                rescalePOSCAR('POSCAR',rescale)
                break;

    if chgcar:
        chgcarnames = ['CHGCAR.gz','CHGCAR','CHGCAR' + calc['file'] + '.gz','CHGCAR' + calc['file']]
        for name in chgcarnames:       
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                density = temp
                out = 'CHGCAR'
                if density[-3:] == '.gz':
                    out += '.gz'
                print('Inheriting charge density from ' + density + '.')
                shutil.copy(density, out)
                if calc['settings']['INCAR'].get('ICHARG') is None:
                    calc['settings']['INCAR']['ICHARG'] = 1
                break;
            
    if wavecar:
        wavecarnames = ['WAVECAR.gz','WAVECAR','WAVECAR' + calc['file']+ '.gz','WAVECAR' + calc['file']]
        for name in wavecarnames:       
            temp = os.path.join(path, name)
            if os.path.isfile(temp):
                wavecar = temp
                out = 'WAVECAR'
                if wavecar[-3:] == '.gz':
                    out += '.gz'
                print('Inheriting wave functions from ' + wavecar + '.')
                shutil.copy(wavecar, out)
                break;
    if grid:
        outcar = os.path.join(path, 'OUTCAR')
        ng = execute('grep "dimension x,y,z NGX" ' + outcar + ' | head -n 1').strip().split()
        calc['settings']['INCAR']['NGX'] = int(ng[4])
        calc['settings']['INCAR']['NGY'] = int(ng[7])
        calc['settings']['INCAR']['NGZ'] = int(ng[10])
              
    if settingsmod:
        presults = manage.getResults(calc['parent'])
        presults['settingsmod'] = settingsmod
        manage.updateResults(presults,calc['parent'])
        print('These setting mods are inherited:')
        print(presults['settingsmod'])
        if settingsmod.get('KPOINTS') is not None and calc['settings'].get('KPOINTS').get('K') is not None:
            curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
            curmod = [int(x) for x in settingsmod['KPOINTS']['K'].split(' ')]
            calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
            print(curkp,curmod)
            print('Calibration update to kpoints executed.')
        if settingsmod.get('INCAR') is not None:
            if settingsmod.get('INCAR').get('ENCUT') is not None:
                calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + settingsmod['INCAR']['ENCUT']

            if settingsmod.get('INCAR').get('SIGMA') is not None:
                calc['settings']['INCAR']['SIGMA'] = settingsmod['INCAR']['SIGMA']

            if settingsmod.get('INCAR').get('ISMEAR') is not None:
                if int(calc['settings']['INCAR']['ISMEAR']) != -5:
                    calc['settings']['INCAR']['ISMEAR'] = settingsmod['INCAR']['ISMEAR']

            if settingsmod.get('INCAR').get('ISPIN') is not None:
                calc['settings']['INCAR']['ISPIN'] = settingsmod['INCAR']['ISPIN']

        #if os.path.isfile('CHGCAR'):
        #    os.rename('CHGCAR','CHGCAR.prec')
    return calc

def abort(cinfo,delay=0,mode = 0):
    # either switch between electronic and ionic or auto based on ibrion is possible
    #for now 0 is electronic stop, 1 ionic
    print('Aborting calculation with delay of ' + str(delay) + ' in dir ' + os.getcwd())
    time.sleep(delay)
    f = open('STOPCAR','w')
    if mode ==0:
        f.write('LABORT=.TRUE.')
    else:
        f.write('LSTOP=.TRUE.')
    f.close()
    open('aborted', 'a').close()
    manage.restart(cinfo['id'])
    psettings = manage.getSettings(manage.calcid)
    if 'continue' in psettings.keys():
        psettings['continue'] = str(int(psettings['continue']) + 1)
    else:
        psettings['continue'] = '1'
    manage.modify({'settings' : psettings, 'id' : manage.calcid})
    return 0


def checkpointStart(cinfo,early=4400):
    walltime = int(os.getenv('PBS_WALLTIME'))
    thread = threading.Thread(target=abort,args=(cinfo,walltime-early,0))
    thread.daemon = True
    thread.start()
    return 0

def cont(calc):
    print('DEBUG: continue')
    baks = 0
    bako = 0
    bakx = 0
    bakt = 0
    bakv = 0

    for file in os.listdir(os.curdir):
        if os.path.isfile(file) and file[0:10] == 'POSCAR.bak':
            baks += 1
        if os.path.isfile(file) and file[0:10] == 'OUTCAR.bak':
            bako += 1
        if os.path.isfile(file) and file[0:11] == 'XDATCAR.bak':
            bakx += 1
        if os.path.isfile(file) and file[0:11] == 'tempout.bak':
            bakt += 1
        if os.path.isfile(file) and file[0:11] == 'vasprun.bak':
            bakv += 1

    if os.path.isfile('CONTCAR') and os.stat('CONTCAR').st_size > 0:
        os.rename('POSCAR','POSCAR.bak' + str(baks))
        os.rename('CONTCAR','POSCAR')
    if os.path.isfile('OUTCAR') and os.stat('OUTCAR').st_size > 0:
        os.rename('OUTCAR','OUTCAR.bak' + str(bako))
    if os.path.isfile('XDATCAR') and os.stat('XDATCAR').st_size > 0:
        os.rename('XDATCAR','XDATCAR.bak' + str(bakx))
    if os.path.isfile('tempout') and os.stat('tempout').st_size > 0:
        os.rename('tempout','tempout.bak' + str(bakt))
    if os.path.isfile('vasprun.xml') and os.stat('vasprun.xml').st_size > 0:
        os.rename('vasprun.xml','vasprun.bak' + str(bakv))
        
    psettings = manage.getSettings(calc['parent'])
    presults = manage.getResults(calc['parent'])
    
    if 'continued' not in psettings.keys():
        psettings['continued'] = 1
    else:
        psettings['continued'] += 1


    if presults.get('settingsmod') is not None:
        if presults['settingsmod'].get('KPOINTS') is not None and calc['settings'].get('KPOINTS') is not None:
            if presults['settingsmod'].get('KPOINTS').get('K') is not None and calc['settings']['KPOINTS'].get('K') is not None:
                curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
                curmod = [int(x) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')]
                calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
    

        if presults.get('settingsmod').get('INCAR') is not None:
            if presults.get('settingsmod').get('INCAR').get('ENCUT') is not None:
                calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + \
                                                     presults['settingsmod']['INCAR']['ENCUT']
            if presults.get('settingsmod').get('INCAR').get('SIGMA') is not None:
                calc['settings']['INCAR']['SIGMA'] = presults['settingsmod']['INCAR']['SIGMA']

            if presults.get('settingsmod').get('INCAR').get('ISMEAR') is not None:
                if int(calc['settings']['INCAR']['ISMEAR']) != -5:
                    calc['settings']['INCAR']['ISMEAR'] = presults['settingsmod']['INCAR']['ISMEAR']

            if presults.get('settingsmod').get('INCAR').get('ISPIN') is not None:
                calc['settings']['INCAR']['ISPIN'] = presults['settingsmod']['INCAR']['ISPIN']

    manage.updateSettings(psettings, calc['parent'])
    manage.updateResults(presults, calc['parent'])

    return calc

def finish():
    #end and readresults, readsettings too possibly, makecif populateresults and convert E/atom etc possibilities of using tables for chemical potentials
    #DOS and bandstructure options here too or in seperate postprocess func
    #Incorporate HTfinish, other httools should go somewhere too
    print('')
    return 0

def initialize(settings,hard = ''):
    #print 'write incar kpoints potcar, make directory?'
    #inherit()
    writeSettings(settings)
    poscar = open('./POSCAR','r')
    lines = poscar.readlines()
    elements = lines[5][:-1].strip()
    execute('POTgen' + str(hard)  + ' ' + str(elements))
    return 0

def prepare(settings):
    #preparing any configs, can turn on SP and SO here too
    parallelSetup(settings)
    #print 'settings should be modified anyways'
    return settings


def getIBZKPT(symmetry=True):
    curdir = os.getcwd()
    if os.path.isdir(os.path.join(curdir, 'genIBZKPT')):
        os.system('rm -rf ' + os.path.join(curdir, 'genIBZKPT'))

    mkdir('genIBZKPT')
    os.chdir(os.path.join(curdir,'genIBZKPT'))
    shutil.copy('../POSCAR','./POSCAR')
    shutil.copy('../POTCAR','./POTCAR')
    shutil.copy('../INCAR','./INCAR')

    if symmetry == False:
        f = open('./INCAR', 'a+')
        f.write('\nISYM=0')
        f.close()

        shutil.copy('../KPOINTS','./KPOINTS')
    genIBZKPT = subprocess.Popen(vasp,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    i = 0
    while(not os.path.isfile(os.path.join(curdir,'genIBZKPT','IBZKPT'))):
        time.sleep(1)
        i+=1
        if i == 600:
            print('IBZKPT NOT GENERATED ERROR')
            os.chdir(curdir)
            os.system('rm -rf ' + os.path.join(curdir, 'genIBZKPT'))
            raise ValueError
    genIBZKPT.terminate()
    f = open('IBZKPT', 'r')
    lines = f.readlines()
    f.close()
    os.chdir(curdir)
    os.system('rm -rf ' + os.path.join(curdir,'genIBZKPT'))

    return int(lines[1].strip())

def detectU(poscar):
    poscar = open(os.path.join(poscar),'r')
    lines = poscar.readlines()
    elements = list(filter(None,lines[5][:-1].lstrip().split(' ')))
    if 'O' in elements or 'F' in elements:
        condition1 = True
    else:
        condition1 = False
    Uel = set(['Co', 'Cr', 'Fe', 'Mn', 'Mo', 'Ni', 'V', 'W'])
    Ldict = {'Co': 2, 'Cr': 2, 'Fe': 2, 'Mn': 2, 'Mo': 2, 'Ni': 2, 'V': 2, 'W': 2}
    Udict = {'Co': 3.32, 'Cr': 3.7, 'Fe': 5.3, 'Mn': 3.9, 'Mo': 4.38, 'Ni': 6.2, 'V': 3.25, 'W': 6.2}
    L = []
    U = []
    J = []

    detels = []
    for el in elements:
        J.append('0.00')
        if el in Ldict.keys() and condition1:
            L.append(str(Ldict[el]))
            U.append(str(Udict[el]))
        else:
            L.append('-1')
            U.append('0.00')
    
    return (' '.join(L), ' '.join(U), ' '.join(J))            


def detectSP(poscar):
    poscar = open(os.path.join(poscar),'r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()
    magel = set(['O','Ni','Cr','Co','Fe','Mn','Ce','Nd','Sm','Eu','Gd','Tb','Dy','Ho','Er','Tm']);
    magnetic = False;

    for magn in magel:
        if magn in elements.split(' '):
             magnetic = True;

    return magnetic

def detectSO(poscar):
    poscar = open(os.path.join(poscar),'r')
    lines = poscar.readlines()
    elements = lines[5][:-1].lstrip()
    relel = set(['Cs','Ba','La','Lu','Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg','Tl','Pb','Bi','Po','At','Rn']);

    relativistic = False;

    for rel in relel:
        if rel in elements.split(' '):
             relativistic = True;

    return relativistic

def run(ratio = 1,cwd = None):
    global vasp
    #could move hybrid to parallel setup
    if cwd is None:
        cwd = os.getcwd();
    nodes = getNodeInfo()

    #cores = mysql_query('SELECT `cores` FROM `clusters` WHERE `name` = ' + str(os.getenv('VSC_INSTITUTE_CLUSTER')))
    hybrid = str(int(min(nodes.values())/int(ratio)))
    total = sum(nodes.values())
    #return execute('mympirun -h ' + hybrid + ' --output ' + cwd + '/tempout ' + vasp)
    print('mpirun -np ' + str(total) + ' ' + vasp + ' > tempout')
    return execute('mpirun -np ' + str(total) + ' ' + vasp + ' > tempout')

def readSettings(settings):
    settings['INCAR'] = readINCAR()
    settings['KPOINTS'] = readKPOINTS()
    POTCAR_version = execute('grep -a \'TITEL\' POTCAR | awk \'{ print $4 }\'')
    settings['POTCAR'] = POTCAR_version.strip().replace('\n',', ')
    #read/writePOTCAR would be useful
    return settings

def parallelSetup(settings):
    try:
        numKP = getIBZKPT()
    except:
        numKP = getIBZKPT(symmetry=False)
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    kpar = min(len(nodes),numKP)

    settings['INCAR']['NCORE'] = ncore
    if 'NPAR' in settings['INCAR'].keys():
        settings['INCAR'].pop('NPAR', None)
    if 'LHFCALC' in settings['INCAR'].keys():
        if settings['INCAR']['LHFCALC'] == '.TRUE.':
            settings['INCAR']['NCORE'] = 1

    #unsure about HFc
    if 'ALGO' in settings['INCAR'].keys():
        if settings['INCAR']['ALGO'][0:2] == 'GW' or settings['INCAR']['ALGO'] == 'ACFDT' or settings['INCAR']['ALGO'] == 'HFc':
            settings['INCAR']['NCORE'] = 1

    settings['INCAR']['KPAR'] = kpar
    return settings

def setupDir(settings):
    #print 'can make potcar and writesettings'
    #inherit too
    writeSettings(settings)
    return 0

def writeSettings(settings):
    writeKPOINTS(settings['KPOINTS'])
    writeINCAR(settings['INCAR'])
    return 0

def eosPrepare(directory = None, evname = 'EOS'):
    if directory is None:
        directory = os.getcwd()
    currentdir = os.getcwd()
    os.chdir(directory)

    if not os.path.isfile('./1.0/POSCAR'):
        return False

    poscar = open('./1.0/POSCAR', 'r')
    lines = poscar.readlines()

    numberofatoms = lines[6][:-1].lstrip()
    numberofatoms = " ".join(numberofatoms.split())
    numberofatoms = sum(map(int, numberofatoms.split(' ')))

    #Setup e-v.dat
    eos = {}
    with open(evname,'w') as eosfile:
        for i in sorted(os.listdir()):
            if os.path.isdir(i) and i.replace('.','',1).isdigit():
                E = execute('grep \'energy  without entropy\'  ' + i + '/OUTCAR | tail -1 | awk \'{ print $7 }\'').strip()
                V = execute('grep vol ' + i + '/OUTCAR | tail -n 1 | awk \'{print $5}\'').strip()
                eos[i] = (float(E)/numberofatoms,V)
                eosfile.write(V + ' ' + str(E) + '\n')
    
    os.chdir(currentdir)
    return eos

def eosFit(directory = None, evname = 'EOS'):
    if directory is None:
        directory = os.getcwd()
    currentdir = os.getcwd()
    os.chdir(directory)
    os.chdir('../')
    
    data = np.loadtxt(evname)

    eos = EquationOfState(data[:,0], data[:,1])
    v0, e0, B, BP, residuals = eos.fit()
    B *=  eos._e * 1.0e21

    outfile = open(evname.replace('.eos','') + '.eosout', 'w')
    if not isinstance(v0,np.float64):
        outfile.write('Could not fit an EOS.')
    else:
        outfile.write('Equation Of State parameters - least square fit of a real Birch Murnaghan curve' + '\n' + '\n')
        outfile.write('V0 \t %.5f \t A^3 \t \t %.4f \t b^3 \n' % (v0,v0/eos.b3))
        outfile.write('E0 \t %.6f \t eV \t \t %.6f \t Ry \n' % (e0,e0/eos.Ry))
        outfile.write('B \t %.3f \t GPa \n' % (B))
        outfile.write('BP \t %.3f \n' % BP)
        outfile.write('\n')
        outfile.write('1-R^2: '+str(residuals)+'\n')
        eos.plot(filename=evname + '.png', show=None)
    outfile.close()



    os.chdir(currentdir)
    return v0, e0, B, BP, residuals

def eosRollback(calc, evname = 'EOS'):
    print('Commencing EOS rollback due to detected errors. ')
    step = int(np.ceil(float(calc['stat'])/2))
    crit = calc['results']['eoscheck']

    edir = crit['dirs'][step].split('/')[-2]
    print('The EOS dir is ' + edir)

    vols = sorted([x.split('/')[-1] for x in crit['dirs'] if edir in x])

    f = open(os.path.join('../',evname), 'r')
    enmin = 999999999.999999999
    i = 0
    for line in f.readlines():
        en = float(line.split()[1])

        if en < enmin:
            enmin = en
            volmin = vols[i]
        i += 1

    os.chdir('../')
    odir = 'old' + str(time.time())
    print('Backing up old EOS in ' + str(odir))

    if not os.path.isdir(odir):
        mkdir(odir)

    for v in vols:
        if os.path.isdir(v):
            shutil.copytree(v, os.path.join(odir,v))
            for i in ['CHGCAR', 'CHGCAR.gz', 'WAVECAR', 'WAVECAR.gz', 'CHG']:
                if os.path.isfile(os.path.join(odir, v, i)):
                    os.remove(os.path.join(odir, v, i))

    for v in [evname, evname + '.eosout',evname + '.png']:
        if os.path.isfile(v):
            shutil.copy(v,os.path.join(odir, v))
            os.remove(v)
    print('DEBUG: volmin', volmin)
    if volmin != '1.0':
        for i in ['CHGCAR','CHGCAR.gz','WAVECAR','WAVECAR.gz','CONTCAR']:
            if os.path.isfile(os.path.join(volmin, i)):
                shutil.copy(os.path.join(volmin, i),os.path.join('1.0', i))

    vols.remove('1.0')

    for v in vols:
        shutil.rmtree(v)

    tstat = int(calc['stat']) - 2*(len(vols) + 1)+1
    print('Rolling back to stat ' + str(tstat))
    parent = mysql_query('SELECT `id` FROM `calculations` WHERE `queue` = ' + str(calc['queue']) + ' AND `file` = ' + calc['file'] + ' AND `stat` = ' + str(tstat))

    psettings = manage.getSettings(parent['id'])
    if 'continue' in psettings.keys():
        psettings['continue'] = str(int(psettings['continue']) + 1)
    else:
        psettings['continue'] = '1'
    manage.modify({'settings': psettings, 'id': parent['id']})

    manage.rollback(tstat, calc['id'])
    resubmit()
    exit()
    return True


def name(potcar):
    name = ''
    for p in potcar:
        temp = (p.split(' ')[-2].split('_')[0])
        name += temp
    return name
def getPotCorr():
    potcorr = json.load(open(os.path.join(os.path.dirname(__file__), '../ML/data/potcarcorr.json')))

    if os.path.isfile('CONTCAR'):
        poscar = open( 'CONTCAR', 'r')
    else:
        poscar = open( 'POSCAR', 'r')
    lines = poscar.readlines()

    species = list(filter(None, subprocess.Popen('grep TITEL POTCAR | awk \'{print $4}\'', stdout=subprocess.PIPE,
                                                 shell=True).communicate()[0].decode().split('\n')))
    numberofatoms = lines[6][:-1].lstrip()
    numberofatoms = " ".join(numberofatoms.split())
    natoms = numberofatoms.split(' ')
    numberofatoms = sum(map(int, natoms))

    corr = 0
    for i in range(len(natoms)):
        corr += float(potcorr[species[i]]) * float(natoms[i])

    corr /= numberofatoms

    return corr


@retry((ValueError, TypeError), tries=3, delay=30, backoff=2)
def getEhull(new=''):
    drone = VaspToComputedEntryDrone()
    queen = BorgQueen(drone, './', 4)
    entriesorig = queen.get_data()
    queen.load_data(os.path.join(os.path.dirname(__file__), '../ML/data/missingels.json'))
    entriesextra = queen.get_data()


    if new != '':
        compat = MaterialsProjectCompatibility(check_potcar=False)
        entriesorig = compat.process_entries(entriesorig)

    for entry in entriesorig:
        name = entry.name
        line = re.findall('[A-Z][^A-Z]*', name.replace('(', '').replace(')', ''))

    searchset = set(re.sub('\d', ' ', ' '.join(line)).split())
    entries = filter(lambda e: set(re.sub('\d', ' ', str(e.composition).replace(' ', '')).split()) == searchset,
                     entriesorig)

    entriesextra = filter(lambda e: set(re.sub('\d', ' ', str(e.composition).replace(' ', '')).split()) & searchset,
                          entriesextra)

    a = MPRester("s2vUo6mzETOHLdbu")
 
    all_entries = a.get_entries_in_chemsys(set(searchset)) + list(entries) + list(entriesextra)

    pd = PhaseDiagram(all_entries)#,None



    for e in pd.stable_entries:
        if e.entry_id == None:
            reaction = pd.get_equilibrium_reaction_energy(e)
            return str(reaction) + ' None'

    for e in pd.unstable_entries:
        decomp, e_above_hull = pd.get_decomp_and_e_above_hull(e)
        pretty_decomp = [("{}:{}".format(k.composition.reduced_formula, k.entry_id), round(v, 2)) for k, v in
                         decomp.items()]
        if e.entry_id == None:
            return str(e_above_hull) + ' ' + str(pretty_decomp)
    #return execute('bash -c \'HTehull ./ ' + new + '\' | tail -n 1')

def gather(results):
    if 'Ehull' in results.keys():
        results['Ehullold'] = 0
        results['potcorr'] = 0
        results['path'] = ''
    resultkeys = list(results.keys()).copy()
    results['Edisp'] = 0

    for key in resultkeys:
        print(key)
        if key[0:2] == 'E0' and 'disp' not in key:
            try:
                vdw = float(execute('grep \'Edisp\' OUTCAR | awk \'{print $3}\''))
            except ValueError:
                vdw = 0
            results['Edisp'] = vdw
            results[key + 'disp'] = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\''))
            results[key] = results[key + 'disp'] - vdw
            if 'atom' in key:
                poscar = open('POSCAR','r')
                lines = poscar.readlines()
        
                numberofatoms = lines[6][:-1].lstrip()
                numberofatoms = " ".join(numberofatoms.split())
                numberofatoms = sum(map(int, numberofatoms.split(' ')))
                results[key] /= numberofatoms
                results[key + 'disp'] /= numberofatoms
        elif key == 'natoms':
            poscar = open('POSCAR','r')
            lines = poscar.readlines()
    
            numberofatoms = lines[6][:-1].lstrip()
            numberofatoms = " ".join(numberofatoms.split())
            numberofatoms = sum(map(int, numberofatoms.split(' ')))
            results[key] = numberofatoms
        elif key == 'Ehull':
            results[key + 'old'] = float(getEhull().split(' ')[0])
            ehull,path = tuple([x.strip() for x in getEhull(new='1').split(' ',maxsplit=1)])
            potcorr = getPotCorr()#float(execute('HTpotcorr ./ 1 | tail -n 1'))
            results[key] = float(ehull) + potcorr
            results['path'] = path
            results['potcorr'] = potcorr
        elif key == 'Eatom':
            #to be implemented
            results[key] = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\''))
            poscar = open('POSCAR', 'r')
            lines = poscar.readlines()

            numberofatoms = lines[6][:-1].lstrip()
            numberofatoms = " ".join(numberofatoms.split())
            numberofatoms = sum(map(int, numberofatoms.split(' ')))
            results[key] /= numberofatoms
            results[key] -= float(execute('HTeatom ./ | tail -n 1'))
        elif key == 'Epure':
            #to be implemented
            results[key] = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\''))
            poscar = open('POSCAR', 'r')
            lines = poscar.readlines()

            numberofatoms = lines[6][:-1].lstrip()
            numberofatoms = " ".join(numberofatoms.split())
            numberofatoms = sum(map(int, numberofatoms.split(' ')))
            results[key] /= numberofatoms
            results[key] -= float(execute('HTepure ./ | tail -n 1'))
        elif key == 'Eelectro':
            results[key] = execute('HTelectro ./')
        elif key == 'cellparams':
            crystal = ase.io.read('CONTCAR')
            results[key] = list(crystal.get_cell_lengths_and_angles())
        elif key == 'volume':
            results[key] = float(execute('grep vol OUTCAR | tail -n 1 | awk \'{print $5}\''))
        elif key == 'eos':
            test = eosPrepare(directory='../')
            if not test:
                continue
            v0, e0, B, BP, residuals = eosFit()
            results[key] = {'V0': v0, 'E0': e0, 'B0': B, 'BP': BP, 'res': residuals}
        elif key == 'BG':
            vr = Vasprun('vasprun.xml',occu_tol=0.1)
            results[key] = vr.eigenvalue_band_properties[0]
        elif key == 'smearerr':
            s0 = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $7 }\''))
            s = float(execute('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $4 }\''))
            results[key] = s0 - s
        elif key == 'magmom':
            magmom = execute('grep number.*magnetization OUTCAR | tail -n 1 | awk \'{print $6}\'').isdigit()
            if isfloat(magmom):
                results[key] = np.abs(float(magmom))
            else:
                results[key] = 0

    return results

def compress():
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    if os.path.isfile('CHGCAR'):
        print('Compressing CHGCAR in ' + os.getcwd() + '.')
        execute('pigz -f -6 -p' + str(ncore) + ' CHGCAR')

    if os.path.isfile('WAVECAR'):
        print('Compressing WAVECAR in ' + os.getcwd() + '.')
        execute('pigz -f -6 -p' + str(ncore) + ' CHGCAR')

def decompress():
    nodes = getNodeInfo()
    ncore = min(nodes.values())
    if os.path.isfile('CHGCAR.gz'):
        print('Decompressing CHGCAR.gz in ' + os.getcwd() + '.')
        execute('pigz -f -d -6 -p' + str(ncore) + ' CHGCAR.gz')

    if os.path.isfile('WAVECAR.gz'):
        print('Decompressing WAVECAR.gz in ' + os.getcwd() + '.')
        execute('pigz -f -d -6 -p' + str(ncore) + ' WAVECAR.gz')

def redivideKP(kp,lc):
    lc = np.array(lc)
    kp = np.array(kp)
    ratio = 1/lc
    total = np.prod(kp)
    newkp = np.array([0,0,0])
    i=0
    ratio /= np.min(ratio)
    ratio = np.round(ratio,0)

    while(np.prod(ratio*newkp) < total):
        newkp = np.round(i*ratio,0)
        newkp += (newkp+1)%2
        i += 1

    return newkp

def setupKP(settings,minkp):
    crystal = ase.io.read('POSCAR')
    cell = crystal.get_cell();
    a = cell[0];
    b = cell[1];
    c = cell[2];
    na = round(norm(a),3);
    nb = round(norm(b),3);
    nc = round(norm(c),3);
    nat = crystal.get_number_of_atoms()
    minkp /= nat

    lc = [na,nb,nc]
    kp = [int(x) for x in settings['KPOINTS']['K'].split()]

    while(np.prod(kp) < minkp):
        kp[0] += 2
        kp[1] += 2
        kp[2] += 2
    kp = redivideKP(kp,lc)

    settings['KPOINTS']['K'] = ' '.join([str(int(x)) for x in kp])
    return settings
    
