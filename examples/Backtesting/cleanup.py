# -*- coding: utf-8 -*-

import HighThroughput.manage.queue as HTq

import pickle

with open('backtest.pkl','rb') as btfile:
    newq, materials = pickle.load(btfile)
    HTq.remove(btfile)
