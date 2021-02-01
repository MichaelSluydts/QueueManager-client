# -*- coding: utf-8 -*-
# Setup a backtesting queue
import HighThroughput.manage.queue as HTq
import HighThroughput.manage.calculation as HTc

from HighThroughput.communication.mysql import mysql_query
import pickle, sys, json

# The target queue we will try predicting
tqueue = sys.argv[1]

# The target status of the final property calculation
tstat = sys.argv[2]

# We use a default 1 step, 3 stat workflow
newq = HTq.add('Backtesting ' + str(tqueue),workflow = 20)

# get all the materials
materials = mysql_query('SELECT `file`, `results` FROM `calculations` WHERE `queue` = ' + str(tqueue) + ' AND `stat` = ' + str(tstat))

# Add them all to our new queue
for mat in materials:
    HTc.add(mat['file'], newq, priority = 1)

# Save the info
with open('backtest.pkl','wb') as btfile:
    pickle.dump((newq,materials),btfile)