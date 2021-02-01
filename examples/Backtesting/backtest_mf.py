# -*- coding: utf-8 -*-

import HighThroughput.manage.queue as HTq
import HighThroughput.manage.calculation as HTc
import HighThroughput.ML.models.priority as HTML
from HighThroughput.communication.mysql import mysql_query
import pickle, sys, json
import random
import numpy as np
import tensorflow as tf

#tf.set_random_seed(666)
#random.seed(666)
#np.random.seed(666)

nsample = 500
stable = 0
#target = sys.argv[1]
rdict = {}
rlist = []
limit = 0.05
N_init = 50
batch_size = 1

newq = 256

target = 'Ehull'

stats = [6, 14, 22, 32, 40, 42]

HTML.updateMLPriority(newq,stat=stats,modelClass= 'sklearn.gaussian_process.GaussianProcessRegressor',target = 'Ehull',features = ['mass','Ecoh','EN','IP']    ,maxParallel=1)
