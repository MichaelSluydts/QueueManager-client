import os
import numpy as np
from HighThroughput.manage.calculation import getResults,updateResults,getSettings
import numpy as np
from HighThroughput.modules.VASP import cont
def test(calc):
    #Dummy
    print('This is a bugfix.')
    return True

def rmWAVECAR(calc):
    #2: CHGCAR more reliable so clear WAVECAR
    if os.path.isfile('WAVECAR'):
        open('WAVECAR', 'w').close() 
        
    if os.path.isfile('WAVECAR.gz'):
        open('WAVECAR.gz', 'w').close()
        
    return True

def rmCHGCAR(calc):
    #7: In case of corrupted density
    if os.path.isfile('CHGCAR'):
        open('CHGCAR', 'w').close()
        
    if os.path.isfile('CHGCAR.gz'):
        open('CHGCAR.gz', 'w').close()
        
    return True

def algoSwitch(calc):
    #3: Switch between All/Damped Normal/Fast
    # Can be tuned by bandgap ismear further
    algos = ['F','N','D','A']
    if calc['settings']['INCAR'].get('ALGO'):
        current = calc['settings']['INCAR']['ALGO'][0]
    else:
        current = 'N'

    try:
        currentindex = algos.index(current)
        calc['settings']['INCAR']['ALGO'] = algos[(currentindex + 1)%4]
        print('Algorithm switched to ' + calc['settings']['INCAR']['ALGO'])
    except ValueError:
        print('Unknown algorithm detected. Skipping algorithm switch.')

    """old
    if 'ALGO' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['ALGO'] = 'Fast'
    elif  calc['settings']['INCAR']['ALGO'][0] == 'F':
        calc['settings']['INCAR']['ALGO'] = 'Normal'
    elif calc['settings']['INCAR']['ALGO'][0] == 'D':
        calc['settings']['INCAR']['ALGO'] = 'A'
    elif calc['settings']['INCAR']['ALGO'][0] == 'A':
        calc['settings']['INCAR']['ALGO'] = 'D'"""
    return True

def halveStep(calc):
    #4: bit much for multiple times, maybe should split
    if 'TIME' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['TIME'] = np.ceil(float(calc['settings']['INCAR']['TIME'])*100.0/2.0)/100.0
    elif 'POTIM' in calc['settings']['INCAR']:
        calc['settings']['INCAR']['POTIM'] = np.ceil(float(calc['settings']['INCAR']['POTIM'])*100.0/2.0)/100.0
    return True


def doubleStep(calc):
    #5: bit much for multiple times
    if 'TIME' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['TIME'] = float(calc['settings']['INCAR']['TIME'])*2.0
    elif 'POTIM' in calc['settings']['INCAR']:
        calc['settings']['INCAR']['POTIM'] = float(calc['settings']['INCAR']['POTIM'])*2.0
    return True

def preconv(calc):
    #8: Preconverge calculation with another algorithm.
    preconvAlgo = {'A' : 'N', 'D' : 'N'}
    calc['settings']['INCAR']['ALGOb'] = calc['settings']['INCAR']['ALGO']
    calc['settings']['INCAR']['ALGO'] = preconvAlgo[calc['settings']['INCAR']['ALGO'][0]]
    calc['settings']['INCAR']['NELMb'] = calc['settings']['INCAR']['NELM'] 
    calc['settings']['INCAR']['NELM'] = '8'
    return True

def restorePreconv(calc):
    #9: Restore the original settings before preconvergence.
    if os.path.isfile('CHGCAR.prec'):
        if os.stat('CHGCAR.prec').st_size > 0:
            os.rename('CHGCAR.prec','CHGCAR')
    if 'ALGOb' in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['ALGO'] = calc['settings']['INCAR']['ALGOb'] 
        del calc['settings']['INCAR']['ALGOb'] 
    if 'NELMb' in calc['settings']['INCAR'].keys(): 
        calc['settings']['INCAR']['NELM'] = calc['settings']['INCAR']['NELMb']
        del calc['settings']['INCAR']['NELMb']
    return True


def doubleNELM(calc):
    if 'NELM' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['NELM'] = 60
    calc['settings']['INCAR']['NELM'] = int(calc['settings']['INCAR']['NELM'])*2
    return True

def halveNELM(calc):
    if 'NELM' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['NELM'] = 60
    calc['settings']['INCAR']['NELM'] = int(calc['settings']['INCAR']['NELM'])/2
    return True

def startWAVECAR(calc):
    #10 Ensure a preconverged WAVECAR is used for the new coefficients and the density.
    calc['settings']['INCAR']['ISTART'] = "1"
    calc['settings']['INCAR']['ICHARG'] = "0"    
    return True

def startCHGCAR(calc):
    calc['settings']['INCAR']['ISTART'] = "0"
    calc['settings']['INCAR']['ICHARG'] = "1"
    return True

def halveSigmaInherit(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = { "INCAR" : {} }
    if 'INCAR' not in presults['settingsmod'].keys():
        presults['settingsmod']['INCAR'] = {}
    elif presults['settingsmod'].get('INCAR').get('SIGMA') != None:
        presults['settingsmod']['INCAR']['SIGMA'] = float(presults['settingsmod']['INCAR']['SIGMA'])/2
    else:
        presults['settingsmod']['INCAR']['SIGMA'] = float(calc['settings']['INCAR']['SIGMA'])/2
    updateResults(presults, calc['parent'])
    return True

def changeSpinInherit(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = { "INCAR" : {} }
    if 'INCAR' not in presults['settingsmod'].keys():
        presults['settingsmod']['INCAR'] = {}
    if presults['settingsmod'].get('INCAR').get('ISPIN') != None:
        presults['settingsmod']['INCAR']['ISPIN'] = (int(presults['settingsmod']['INCAR']['ISPIN'])-2) % 2 + 1
    else:
        presults['settingsmod']['INCAR']['ISPIN'] = (int(calc['settings']['INCAR']['ISPIN'])-2) % 2 + 1
    print('Setting spin to ' + str(presults['settingsmod']['INCAR']['ISPIN']))
    updateResults(presults, calc['parent'])
    return True

def changeSmearInherit(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = {"INCAR": {}}
    if 'INCAR' not in presults['settingsmod'].keys():
        presults['settingsmod']['INCAR'] = {}

    if presults['settingsmod'].get('INCAR').get('ISMEAR') != None:
        if presults['settingsmod'].get('INCAR').get('ISMEAR') == 0:
            presults['settingsmod']['INCAR']['ISMEAR'] = 1
            presults['settingsmod']['INCAR']['SIGMA'] = 0.2
        elif presults['settingsmod'].get('INCAR').get('ISMEAR') == 1:
            presults['settingsmod']['INCAR']['ISMEAR'] = 0
            presults['settingsmod']['INCAR']['SIGMA'] = 0.05
    else:
        if calc['settings']['INCAR']['ISMEAR'] == 0:
            presults['settingsmod']['INCAR']['ISMEAR'] = 1
            presults['settingsmod']['INCAR']['SIGMA'] = 0.2
        elif calc['settings']['INCAR']['ISMEAR'] == 1:
            presults['settingsmod']['INCAR']['ISMEAR'] = 0
            presults['settingsmod']['INCAR']['SIGMA'] = 0.05
    updateResults(presults, calc['parent'])
    return True

def converge(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = {}
        
    for propset in presults['convergence']:
        total = len(propset)
        prop = propset[0]
        for i in range(1,total):
            (crit,cond,current,converged) = propset[i]
            if converged == 1:
                continue;
            elif crit == 'K':
                if 'KPOINTS' not in presults['settingsmod'].keys():
                    presults['settingsmod']['KPOINTS'] = {}
                if 'K' not in presults['settingsmod']['KPOINTS'].keys():
                    presults['settingsmod']['KPOINTS']['K'] = '2 2 2'
                else:
                    presults['settingsmod']['KPOINTS']['K'] = ' '.join([str(int(x) + 2) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')])
            #curkp = [int(x) for x in calc['settings']['KPOINTS']['K'].split(' ')]
           #curmod = [int(x) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')]
             #   calc['settings']['KPOINTS']['K'] = ' '.join([str(curkp[x] + curmod[x]) for x in range(3)])
                break;
            elif crit == 'ENCUT':
                if 'INCAR' not in presults['settingsmod'].keys():
                    presults['settingsmod']['INCAR'] = {}
                if 'ENCUT' not in presults['settingsmod']['INCAR']:
                    presults['settingsmod']['INCAR']['ENCUT'] = 100
                else:
                    presults['settingsmod']['INCAR']['ENCUT'] += 100
              #  calc['settings']['INCAR']['ENCUT'] = int(calc['settings']['INCAR']['ENCUT']) + presults['settingsmod']['INCAR']['ENCUT']
                break;
    updateResults(presults,calc['parent'])
    return True

def lowerSYMPREC(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = {}

    if 'SYMPREC' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['SYMPREC'] = 1e-5
    if 'INCAR' not in presults['settingsmod'].keys():
        presults['settingsmod']['INCAR'] = {}
    if 'ENCUT' not in presults['settingsmod']['INCAR']:
        presults['settingsmod']['INCAR']['SYMPREC'] = np.float32(calc['settings']['INCAR']['SYMPREC'])/10.
    else:
        presults['settingsmod']['INCAR']['SYMPREC'] = np.float32(calc['settings']['INCAR']['SYMPREC'])/10.
    return True


def raiseSYMPREC(calc):
    presults = getResults(calc['parent'])
    if 'settingsmod' not in presults.keys():
        presults['settingsmod'] = {}

    if 'SYMPREC' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['SYMPREC'] = 1e-5
    if 'INCAR' not in presults['settingsmod'].keys():
        presults['settingsmod']['INCAR'] = {}
    if 'ENCUT' not in presults['settingsmod']['INCAR']:
        presults['settingsmod']['INCAR']['SYMPREC'] =  np.float32(calc['settings']['INCAR']['SYMPREC'])*10.
    else:
        presults['settingsmod']['INCAR']['SYMPREC'] = np.float32(calc['settings']['INCAR']['SYMPREC'])*10.
    return True

def toggleISYM(calc):
    presults = getResults(calc['parent'])
    if 'ISYM' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['ISYM'] = 1

    calc['settings']['INCAR']['ISYM'] =  (int(calc['settings']['INCAR']['ISYM']) + 1) %2
    return True

def contCalc(calc):
    return True
