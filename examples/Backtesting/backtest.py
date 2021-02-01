# -*- coding: utf-8 -*-

import HighThroughput.manage.queue as HTq
import HighThroughput.manage.calculation as HTc
import HighThroughput.ML.models.priority as HTML
from HighThroughput.communication.mysql import mysql_query
import pickle, sys, json
import random
import numpy as np
import tensorflow as tf

tf.set_random_seed(666)
random.seed(666)
np.random.seed(666)

nsample = 500
stable = 0
#target = sys.argv[1]
rdict = {}
rlist = []
limit = 0.05
N_init = 50
batch_size = 1

newq = 251

target = 'Ehull'

#with open('backtest.pkl','rb') as btfile:
#    newq, materials = pickle.load(btfile)

materials = mysql_query('SELECT `file`, `Ehull` FROM `zintlfinal` WHERE `queue` = 239')

for mat in materials:
    #result = json.loads(mat['results'])
    rdict[mat['file']] = float(mat[target])

tstable = sum([1 for x in rdict.values() if float(x) < limit])
print('There are ' + str(tstable) + ' stable materials to find in this queue.')

#HTML.setMLPriority(newq,stat=2)

#HTML.setMLPriority(newq, 2,  ['mass','Ecoh','EN','IP'], N_init)
#
#for i in range(N_init):
#    calc = HTc.fetchgetstart(newq)
#    HTc.updateResults({target: rdict[calc['file']]})
#
#    if rdict[calc['file']] < limit:
#        stable += 1
#    print('Found ' + str(stable) + ' stable materials (' + str(int(round(100*stable/tstable,0))) + ' %) in ' + str(i+1) + ' samples.')
#    HTc.end()
    
for i in range(nsample):
    if i%batch_size==0:
        HTML.updateMLPriority(newq,stat=2,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target = 'Ehull',features = ['mass','Ecoh','EN','IP']    ,maxParallel=1)
    calc = HTc.fetchgetstart(newq)
    print(calc)
    HTc.updateResults({target: rdict[calc['file']]})

    if rdict[calc['file']] < limit:
        stable += 1
    print('Found ' + str(stable) + ' stable materials (' + str(int(round(100*stable/tstable,0))) + ' %) in ' + str(i+1) + ' samples.')
    HTc.end()