from mendeleev import element
import numpy as np
from sqlalchemy import create_engine
import pandas as pd
        
def compute_volume(poscar_lines):
    unit_vec1 = np.expand_dims(np.array(poscar_lines[2].split(), dtype=float),axis = 1)
    unit_vec2 = np.expand_dims(np.array(poscar_lines[3].split(), dtype=float),axis = 1)
    unit_vec3 = np.expand_dims(np.array(poscar_lines[4].split(), dtype=float),axis = 1)
    unit_mat = np.concatenate((unit_vec1, unit_vec2, unit_vec3), axis = 1)
    
    return np.abs(np.linalg.det(unit_mat))

def compute_volume_atoms(poscar_lines, atoms_vol):
    elements_all   = poscar_lines[5].split()
    elements_count = np.asarray(poscar_lines[6].split(), dtype=float)
    atoms_vols     =  [atoms_vol[element_old] for element_old in elements_all]
    volume_atoms = sum([atom_vols*element_count for atom_vols, element_count in zip(atoms_vols, elements_count)])
    
    return volume_atoms

def basicVolume():

    filename = #TODO: add POSCAR prototype
    
    with open(path + filename) as input_file:
        old_lines = input_file.readlines()
        
    volume_org = compute_volume(old_lines)
    
    volume_org_atoms = compute_volume_atoms(old_lines, atoms_vol)
    
    rescale = volume_org/volume_org_atoms
    
    volume_est  = []
    
    filenames = #TODO: add composition new materials
    
    for filename in filenames:
        if int(filename.split('\\')[-1][6:]) in indices_239:
            with open(filename) as input_file:
                lines_new    = input_file.readlines()
            elements_new = lines_new[5].split()
            volume_atoms = compute_volume_atoms(lines_new, atoms_vol)
            
            volume_est.append(volume_atoms*rescale)
            
    return np.array(volume_est)
