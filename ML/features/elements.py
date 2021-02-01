# -*- coding: utf-8 -*-
"""
Created on Thu Jul 26 15:28:56 2018

@author: Michiel
"""

# -*- coding: utf-8 -*-
from HighThroughput.communication.mysql import mysql_query
import pandas as pd

def addElemental_old(df,features):

    ncols = len([1 for feat in list(df) if feat.find('el')==0])
    els = set([])

    for i in range(ncols):
        els = els.union(set(df['el' + str(i)].unique()))
    
    allfeats = ['atomicnumber','symbol','mass','Ecoh','n','s','p','d','V','r','EN','EA','IP']

    atominfo = mysql_query('SELECT * FROM `elements` WHERE `symbol` IN (\'' + '\',\''.join(els) + '\')')
    atomdict = {}
    
    for row in atominfo:
        for f in allfeats:
            if f not in atomdict:
                atomdict[f] = []
            atomdict[f].append(row[f])
    
    atoms = pd.DataFrame(atomdict,columns=allfeats)
    data = {}

    for col in features:
        for i in range(ncols):
            data[col + str(i)] = [0 for x in range(0,len(df))]
            
    new = pd.DataFrame(data,index=df.index)
    
    df = pd.concat([df,new], axis=1)

    for (ind,material) in df.iterrows():
        for i in range(ncols):
            atominfo = atoms.loc[atoms['symbol'] == material['el' + str(i)]]
            for col in features:
                df.loc[ind,col + str(i)] = float(atominfo[col].values[0])
                
    return df

def addElemental(df,features):
    ncols = len([1 for feat in list(df) if feat.find('el')==0])
    els = set([])

    for i in range(ncols):
        els = els.union(set(df['el' + str(i)].unique()))
    
    allfeats = ['atomicnumber','symbol','mass','Ecoh','n','s','p','d','V','r','EN','EA','IP']

    atominfo = mysql_query('SELECT * FROM `elements` WHERE `symbol` IN (\'' + '\',\''.join(els) + '\')')
    atomdict = {}
    
    for row in atominfo:
        for f in allfeats:
            if f not in atomdict:
                atomdict[f] = []
            atomdict[f].append(row[f])
    
    atoms = pd.DataFrame(atomdict,columns=allfeats)
    data = [[0 for i in range(ncols*len(features))] for j in  range(len(df))]

    index_df = pd.Index(df.index)
    
    column_names = ["name" for i in range(ncols*len(features))]
    
    for (ind,material) in df.iterrows():
      for i in range(ncols):
        atominfo = atoms.loc[atoms['symbol'] == material['el' + str(i)]]
        row_loc = index_df.get_loc(ind)
        for ind_feat, col in enumerate(features):
          col_loc = i+ncols*ind_feat
          column_names[col_loc] = col+str(i)
          data[row_loc][col_loc] = float(atominfo[col].values[0])

    new = pd.DataFrame(data,index=df.index, columns = column_names)
    
    df = pd.concat([df,new], axis=1)
                
    return df    
