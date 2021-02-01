from HighThroughput.communication.mysql import *
import HighThroughput.io.CIF as CIF
import os
import ase.io
from numpy.linalg import norm
from numpy import dot, arccos, degrees

def get(cifid):
    if int(cifid) < 10000000:
        table = 'data'
    else:
        table = 'newdata'
    return mysql_query('SELECT * FROM `' + table + '` WHERE `file` = ' + str(cifid))

def importdir(directory=os.getcwd()):
    i=0;
    os.chdir(directory)
    for filename in os.listdir(directory):
        if os.path.isdir(directory + '/' + filename):
            importdir(directory + '/' + filename);
        else:
            val = add(filename)
            if val != 0:
                i = i+1
    return i

def importdirbatch(directory=os.getcwd(),group=None,description='No description provided.'):
    owner = mysql_query('')

    if group is None:
        group = mysql_query('INSERT INTO mgroups (`owner`, `description`) VALUES (' + str(owner) + ',' + str(description) + ')')
    print('The materials group is ' + str(group))
    i=0;
    os.chdir(directory)
    filenames = []
    for filename in os.listdir(directory):
        if os.path.isdir(directory + '/' + filename):
            importdir(directory + '/' + filename);
        else:
            filenames.append(filename)
    return batchadd(filenames,group)

def modify(params):
    query = 'UPDATE `newdata` SET '
    for key in params.keys():
        if key != 'file':
            query += '`' + key  + '` ='
            if not str(params[key]).isdigit():
                query += '\'' + str(params[key]) + '\''
            else:   
                query += str(params[key])
            query += ', ' 
    query = query[:-2] + ' WHERE `file` = ' + str(params['file'])
    result = mysql_query(query)
        
    if (result == '1'):
        print('The calculation has been modified. Please verify.')
    elif (result == '0'):
        print('Nothing to modify.')
    else:   
        print('Help... Me...')
    return result


def batchadd(filenames,group):
    query = ''
    owner = mysql_query('')
    name = mysql_query('SELECT `name` FROM `accounts` WHERE `id` = ' + owner)
    i=0
    for filename in filenames:
        title = filename.rsplit('.', 2);
        print(filename)
        if not title[0].isdigit():
            crystal = ase.io.read(filename);
        else:
            continue

        elements = crystal.get_chemical_symbols();
        unique = set(elements);

        for el in unique:
            el = el + str(elements.count(el));

        unique = [el + str(elements.count(el)) for el in unique];
        unique = ' '.join(unique);

        cell = crystal.get_cell();
        a = cell[0];
        b = cell[1];
        c = cell[2];
        na = round(norm(a), 3);
        nb = round(norm(b), 3);
        nc = round(norm(c), 3);
        alpha = round(degrees(arccos(dot(b, c) / nb / nc)), 1);
        beta = round(degrees(arccos(dot(c, a) / nc / na)), 1);
        gamma = round(degrees(arccos(dot(a, b) / na / nb)), 1);
        volume = round(crystal.get_volume(), 3);

        CIFtext = CIF.write('temp.cif', crystal)
        os.remove('temp.cif')


        query += 'INSERT INTO newdata (`a`, `b`, `c`, `alpha`, `beta`, `gamma`, `vol`, `celltemp`, `formula`, `calcformula`, `authors`, `year`, `text`, `owner`, `cif`,`mgroup`) VALUES (' + str(na) + ', ' + str(nb) + ', ' + str(nc) + ',' + str(alpha) + ', ' + str(beta) + ', ' + str(gamma) + ',' + str(volume) + ', 0, \'' + unique + '\', \'' + unique + '\', \'' + name['name'] + '\', 2012,\'' + title[0].replace('POSCAR', '').replace('.com', '') + '\', ' + owner + ',\'' + CIFtext.replace('\'','\\\'') + '\', ' + str(group) + ');'

        i += 1
        if i % 100 == 0:
            result = mysql_query(query);
            print(result)
            query = ''

            cifid = result

            if int(result) > 0:
                print('Inserted  batch ' + str(i) + ' into the materials database.')
            else:
                print('Insert failed on batch ' + str(i) + '.')
    result = mysql_query(query);
    print(result)
    query = ''

    cifid = result

    if int(result) > 0:
        print('Inserted  batch ' + str(i) + ' into the materials database.')
    else:
        print('Insert failed on batch ' + str(i) + '.')
    return cifid

def add(filename):
    title = filename.rsplit('.',2);
    print(filename) 
    if not title[0].isdigit():
        crystal = ase.io.read(filename);
    else:
        return 0

    elements = crystal.get_chemical_symbols();
    unique = set(elements);
    
    for el in unique:
        el = el + str(elements.count(el));
    
    unique = [el + str(elements.count(el)) for el in unique];
    unique= ' '.join(unique);

    cell = crystal.get_cell();
    a = cell[0];
    b = cell[1];
    c = cell[2];
    na = round(norm(a),3);
    nb = round(norm(b),3);
    nc = round(norm(c),3);
    alpha = round(degrees(arccos(dot(b,c)/nb/nc)),1);
    beta = round(degrees(arccos(dot(c,a)/nc/na)),1);
    gamma = round(degrees(arccos(dot(a,b)/na/nb)),1);
    volume = round(crystal.get_volume(),3); 
    
    CIFtext = CIF.write('temp.cif',crystal)
    os.remove('temp.cif')

    owner = mysql_query('')
    name = mysql_query('SELECT `name` FROM `accounts` WHERE `id` = ' + owner)
    
    result = mysql_query('INSERT INTO newdata (`a`, `b`, `c`, `alpha`, `beta`, `gamma`, `vol`, `celltemp`, `formula`, `calcformula`, `authors`, `year`, `text`, `owner`, `cif`) VALUES (' + str(na) + ', ' + str(nb) + ', ' + str(nc) + ',' + str(alpha) + ', ' + str(beta) + ', ' + str(gamma) + ',' + str(volume) + ', 0, \'' + unique + '\', \'' + unique + '\', \'' + name['name'] + '\', 2012,\'' + title[0].replace('POSCAR','').replace('.com','') + '\', ' + owner + ',\'' + CIFtext.replace('\'','\\\'') + '\')');
    cifid = result
    if int(result) > 0:
        print('Inserted ' + title[0].replace('POSCAR','').replace('.com','') + ' into the materials database as cif ' + str(cifid) + '.')
    else:
        print('Insert failed.')
    if len(title) > 1:
        os.rename(filename,str(cifid) + '.' + title[1]);
    else:
        os.rename(filename,str(cifid));
    return cifid
