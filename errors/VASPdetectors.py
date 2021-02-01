import subprocess, os, json
from HighThroughput.manage.calculation import getResults, getSettings, updateResults
from HighThroughput.modules.VASP import gather, eosRollback
from HighThroughput.utils.generic import execute
import numpy as np
from pymatgen.io.vasp.outputs import Vasprun
from pymatgen.electronic_structure.core import Spin, Orbital
import xml
import shutil

def currenterror(calc):
    if len(calc['cerrors']) > 0:
        print('Skipping current step due to detected errors.')
        return True

def test(calc):
    print('SEARCHING FOR ERRORS')
    det = int(
        subprocess.Popen('grep WAAAAAAAAAGH tempout | wc -l', shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if det > 0:
        print('Error detected.')
        return True
    else:
        return False


def maxSteps(calc):
    # Slow, bad or no convergence
    nsteps = subprocess.Popen(
        'grep -e "  .*  .*  .*  .*  .*  .*" OSZICAR | grep : | grep -v vasp | awk \'{print $2}\' | tail -n 1',
        shell=True, stdout=subprocess.PIPE).communicate()[0].decode().strip()

    if nsteps.isdigit():
        nsteps = int(nsteps)
    else:
        return False
    if 'NELM' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['NELM'] = 60

    print(str(nsteps) + ' performed of ' + str(calc['settings']['INCAR']['NELM']) + ' allowed steps')

    if nsteps == int(calc['settings']['INCAR']['NELM']):
        print('Error detected.')
        return True
    else:
        return False

def maxIonicSteps(calc):
    # Slow, bad or no convergence
    nsteps = subprocess.Popen(
        'grep F= tempout | awk \'{print $1}\' | tail -n 1',
        shell=True, stdout=subprocess.PIPE).communicate()[0].decode().strip()

    if nsteps.isdigit():
        nsteps = int(nsteps)
    else:
        return False
    if 'NSW' not in calc['settings']['INCAR'].keys():
        calc['settings']['INCAR']['NSW'] = 0

    if nsteps == 0:
        return False
    if 'IBRION' not in calc['settings']['INCAR'].keys():
        return False
    elif int(calc['settings']['INCAR']['IBRION']) <= 0:
        return False

    print(str(nsteps) + ' performed of ' + str(calc['settings']['INCAR']['NSW']) + ' allowed ionic steps')

    if nsteps == int(calc['settings']['INCAR']['NSW']):
        print('Error detected.')
        return True
    else:
        return False



def gradNotOrth(calc):
    # Corrupted CHGCAR, POTCAR or optimizer/lib issue in VASP
    detected = int(
        subprocess.Popen('fgrep "EDWAV: internal error, the gradient is not orthogonal" tempout | wc -l', shell=True,
                         stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def ZHEGV(calc):
    # Davidson failing
    detected = int(subprocess.Popen('fgrep "Error EDDDAV: Call to ZHEGV failed." tempout | wc -l', shell=True,stdout=subprocess.PIPE).communicate()[0].decode().strip())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def subSpace(calc):
    # Davidson failing more
    detected = int(subprocess.Popen('fgrep "Sub-Space-Matrix is not hermitian in DAV" tempout | wc -l', shell=True,stdout=subprocess.PIPE).communicate()[0].decode().strip())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def planeWaveCoeff(calc):
    # Grid/basis set/whatnot changed
    detected = int(
        subprocess.Popen('fgrep "ERROR: while reading WAVECAR, plane wave coefficients changed" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def corruptWAVECAR(calc):
    # Grid/basis set/whatnot changed
    detected = int(
        subprocess.Popen('fgrep "ERROR: while reading eigenvalues from WAVECAR" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def SGRCON(calc):
    # Grid/basis set/whatnot changed
    detected = int(
        subprocess.Popen('fgrep "VERY BAD NEWS! internal error in subroutine SGRCON" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode()) + int(
        subprocess.Popen('fgrep "SYMPREC" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def ZPOTRF(calc):
    # Grid/basis set/whatnot changed
    detected = int(subprocess.Popen('fgrep "LAPACK: Routine ZPOTRF failed!" tempout | wc -l', shell=True,
                                    stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False


def PSSYEVX(calc):
    # Grid/basis set/whatnot changed
    detected = int(
        subprocess.Popen('fgrep "ERROR in subspace rotation PSSYEVX: not enough eigenvalues found" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def SYMPREC(calc):
    # error with symmetry, currently not used, combined with SGRCON
    detected = int(
        subprocess.Popen('fgrep "SYMPREC" tempout | wc -l',
                         shell=True, stdout=subprocess.PIPE).communicate()[0].decode())
    if detected > 0:
        print('Error detected.')
        return True
    else:
        return False

def energyMissing(calc):
    # Energy cannot be extracted from OUTCAR
    # Is not in de db
    energy = int(
        subprocess.Popen('grep \'energy  without entropy\'  OUTCAR | tail -1 | awk \'{ print $8 }\'', shell=True,
                         stdout=subprocess.PIPE).communicate()[0].decode()).strip()
    if energy == '' or not 'energy' in locals():
        print('Error detected.')
        return True
    else:
        return False


def chgMissing(calc):
    if not os.path.isfile('CHGCAR') or not os.path.isfile('CHG'):
        print('Error detected.')
        return True
    else:
        return False


def smearErr(calc):
    if int(calc['settings']['INCAR']['ISMEAR']) != 1:
        return False

    if currenterror(calc):
        return False

    if '9' in calc['cerrors']:
        print('Skipping sigma check due to smearing change.')
        return False

    psettings = getSettings(calc['parent'])
    results = gather({'natoms': 0, 'smearerr': 0})
    if float(results['smearerr']) > 0.001 * float(results['natoms']):
        print('Detected a smearing error of size: ' + str(results['smearerr']))
        return True
    else:
        return False


def wrongSmear(calc):
    if os.path.isfile('aborted'):
        return False

    if currenterror(calc):
        return False

    try:
        vasprun = Vasprun('vasprun.xml')
    except xml.etree.ElementTree.ParseError as e:
        shutil.copy2('vasprun.xml','error.vasprun.xml')
        raise ValueError

    index = np.argmin(np.abs(vasprun.idos.energies - vasprun.efermi))
    index01 = np.argmin(np.abs(vasprun.idos.energies - vasprun.efermi - 0.1))
    dos = np.sum([int(float(x) < 0.5) for x in vasprun.tdos.densities[Spin.up][index:index01]])
    diff = vasprun.idos.densities[Spin.up][index01] - vasprun.idos.densities[Spin.up][index]
    print(diff)
    print(dos)
    psettings = getSettings(calc['parent'])
    smearing = calc['settings']['INCAR']['ISMEAR']
    if 'continue' in psettings.keys():
        doubt = int(psettings['continue'])
        print(doubt,smearing)
        if (doubt > 5) and smearing == 1:
            return True
        elif (doubt > 5) and smearing == 0:
            return False
    # Could check if Gamma is in the k-mesh to estimate the odds of a missed BG crossing
    if (smearing == 0 and diff - 0.5 > -1e-3) or (smearing == 1 and diff - 0.5 < -1e-3 and dos > 0.):
        print('Wrong smearing detected.')
        # if (smearing == 0 and diff <= 0.03) or (smearing == 1 and BG > 0.03):
        return True
    else:
        return False

def checkSpin(calc):
    #needs lorbit option
    if currenterror(calc):
        return False
    if ('spincheck' not in calc['results'].keys()) or (calc['settings']['INCAR']['ISPIN'] == 1):
        return False

    magmom = gather({'magmom' : 0})['magmom']

    if magmom < calc['results']['spincheck']:
        print('Unnecessary spin detected.')
        return True
    return False

def notConverged(calc):
    if os.path.isfile('aborted'):
        return False

    if len(calc['cerrors']) > 0:
        print('Skipping convergence step due to detected errors.')
        return False

    presults = getResults(calc['parent'])
    error = False

    if 'convergence' not in presults.keys():
        return False
    else:
        # "convergence": [["Ehull", ["K", 0.01, [], 0]]] format, could add more than two els to each tuple to determine how to increase the settings and so on
        new = []
        for propset in presults['convergence']:
            total = len(propset)
            prop = propset[0]
            pnew = (prop,)
            for i in range(1, total):
                (crit, cond, current, converged) = propset[i]
                if converged == 1:
                    propset[i][-1] = 1
                    pnew += (tuple(propset[i]),)
                    #print('converged?', pnew)
                    continue;
                print('Checking ' + prop + ' convergence ' + ' with respect to ' + crit + '.')

                newval = gather({prop: ''})[prop]

                current.append(newval)

                if len(current) == 1:
                    error = True
                else:

                    delta = np.abs(current[-1] - current[-2])

                    if delta > cond:
                        print('Not converged. Remaining error of ' + str(delta) + ' on ' + prop + '.')
                        error = True
                    else:
                        print('Property ' + prop + ' is converged up to ' + str(delta) + '.')
                        if crit == 'K':
                            presults['settingsmod']['KPOINTS']['K'] = ' '.join(
                                [str(int(x) - 2) for x in presults['settingsmod']['KPOINTS']['K'].split(' ')])
                        elif crit == 'ENCUT':
                            presults['settingsmod']['INCAR']['ENCUT'] -= 100
                        converged = 1
                pnew += ((crit, cond, current, converged),)
            new.append(pnew)
    # presults['convergence'] = json.dumps(new).translate(str.maketrans({"'":  r"\'"}))
    updateResults(presults, calc['parent'])
    return error

def eosCheck(calc):
    if 'eoscheck' not in calc['results'].keys():
        return False

    eos = gather({'eos' : {}})['eos']
    crit = calc['results']['eoscheck']
    error = False

    if np.iscomplex(eos.values()).any():
        error = True
    if error:
        print('EOS Check: Complex number returned by fit.')
        return error
    else:
        print('No complex values:')
        print(eos)

    if crit['res'] is not None:
        if eos['res'] > crit['res']:
            print('EOS Check: Residual test failed with value 1-r^2 = ' + str(eos['res']) + ' for material ' + calc['file'])
            error = True

    if crit['B0'] is not None:
        if (eos['B0'] < crit['B0'][0]) or (eos['B0'] > crit['B0'][1]):
            print('EOS Check: Bulk modulus test failed with value B0 = ' + str(eos['B0']) + ' for material ' + calc['file'])
            error = True

    if crit['BP'] is not None:
        if (eos['BP'] < crit['BP'][0]) or (eos['BP'] > crit['BP'][1]):
            print('EOS Check: Bulk modulus derivative test failed with value BP = ' + str(eos['BP']) + ' for material ' + calc['file'])
            error = True

    if crit['V0'] is not None:
        if isinstance(eos['V0'], np.float64):
            if (eos['V0'] < crit['V0'][0]) or (eos['V0'] > crit['V0'][1]):
                print('EOS Check: Volume test failed with value V0 = ' + str(eos['V0'])  + ' for material ' + calc['file'])
                error = True
        else:
            error = True

    if error == True:
        eosRollback(calc)

    return error
