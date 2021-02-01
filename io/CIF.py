import ase.io
import os

def read(name,software='VASP',directory=None):
    if directory == None:
        directory = os.getcwd()
    olddir = ''
    if(directory != os.getcwd()):
        olddir = os.getcwd()
        os.chdir(directory)

    fileform = {'VASP' : 'vasp', 'Gaussian' : 'gaussian'};
    CIF = ase.io.read(name,format=fileform[software])
    if olddir:
        os.chdir(olddir)
    return CIF

def write(name,CIF,directory=None):
    olddir = ''
    if directory == None:
        directory = os.getcwd()
    if(directory != os.getcwd()):
        olddir = os.getcwd()
        os.chdir(directory)
    ase.io.write(name, CIF, format='cif')
    if olddir:
        os.chdir(olddir)

    with open (name, 'r') as CIFfile:
        return CIFfile.read()
