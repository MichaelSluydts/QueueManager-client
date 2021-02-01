# -*- coding: utf-8 -*-
from HighThroughput.communication.mysql import mysql_query
import pandas as pd
import json
import re
columns_elements = {'Na': 1, 'K' : 1, 'Rb': 1, 'Cs': 1,
            'Mg': 2, 'Ca': 2, 'Sr': 2, 'Ba': 2,
            'Al': 3, 'Ga': 3, 'In': 3, 'Tl': 3,
            'Si': 4, 'Ge': 4, 'Sn': 4, 'Pb': 4,
            'P' : 5, 'As': 5, 'Sb': 5, 'Bi': 5,
            'S' : 6, 'Se': 6, 'Te': 6}

def _gcd (a,b):
    if (b == 0):
        return a
    else:
         return _gcd (b, a % b)
            
def _get_gcd(array):
  res = array[0]
  for c in array[1::]:
      res = _gcd(res , c)
  return res
  
def getComposition(queue,stat):
#    rows = mysql_query('SELECT `calculations`.`file` AS `file`, `calculations`.`id` AS `id`, `newdata`.`formula` AS `formula` FROM `calculations` INNER JOIN `newdata` ON `calculations`.`file`=`newdata`.`file` WHERE `calculations`.`queue` = ' + str(queue) + ' AND `calculations`.`stat` = ' + str(stat))
    rows = mysql_query('SELECT `calculations`.`file` AS `file`, `calculations`.`id` AS `id`, `newdata`.`text` AS `text` FROM `calculations` INNER JOIN `newdata` ON `calculations`.`file`=`newdata`.`file` WHERE `calculations`.`queue` = ' + str(queue) + ' AND `calculations`.`stat` = ' + str(stat))
    
    if type(rows) != list:
        return [rows]
    compdict = {'id' : []}
    for row in rows:
        compdict['id'].append(row['id'])
        
#        formula = row['formula'].split()
        formula = re.findall('[A-Z][^A-Z]*', row['text'])
#        print(formula)
        stoich  = [[int(i) for i in x if i.isdigit()] for x in formula]
        stoich = [x if len(x)>0 else [1] for x in stoich]
        stoich = [sum([i*10**(len(x)-ind-1) for ind, i in enumerate(x)]) for x in stoich]
        els = [ ''.join([i for i in x if not i.isdigit()]) for x  in formula]
#        ids_reordered = sorted(range(len(els)), key=[columns_elements[el] for el in els].__getitem__)
        
#        gcd = _get_gcd(stoich)
        
#        stoich = [int(stoich[id]/gcd) for id in ids_reordered]
#        els    = [els[id]    for id in ids_reordered]   
        if len(els) == 3:
            els.append('He')
            stoich.append(0)
        for i in range(len(els)):
            if 'el' + str(i) not in compdict:
                compdict['el' + str(i)] = []
                compdict['stoich' + str(i)] = []
            
            compdict['el' + str(i)].append(els[i])
            compdict['stoich' + str(i)].append(stoich[i])
    composition = pd.DataFrame(compdict)
    composition.fillna(0)
    return composition
    
def getFile(queue,stat):
     rows = mysql_query('SELECT `file` FROM `calculations` WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
        
     file = []
     
     for row in rows:
        file.append(row['file'])
        
     file = pd.DataFrame({'file' : file})
     return file


def getID(queue,stat):
     rows = mysql_query('SELECT `id` FROM `calculations` WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
        
     cid = []
     
     for row in rows:
        cid.append(row['id'])
        
     ID = pd.DataFrame({'id' : cid})
     return ID
 
def getResults(queue,stat,keys):
    rows = mysql_query('SELECT `file`, `results` FROM `calculations` WHERE `queue` = ' + str(queue) + ' AND `stat` = ' + str(stat))
    
    keys.insert(0,'file')
    
    resultsdict = { 'file' : []}
    
    for key in keys:
        resultsdict[key] = []
        
    for row in rows:
        resultsdb = json.loads(row['results'])
        for key in keys:
            if key == 'file':
                resultsdict[key].append(row[key])
            else: 
                resultsdict[key].append(resultsdb[key])
        
    results = pd.DataFrame(resultsdict)
    return results
