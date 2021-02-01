# -*- coding: utf-8 -*-
from HighThroughput.communication.mysql import mysql_query
import pickle

#with open('backtest.pkl','rb') as btfile:
#    newq, materials = pickle.load(btfile)

newq = 251 

mysql_query('DELETE FROM `calculations` WHERE `queue` = ' + str(newq) + ' AND `stat` > 0')
mysql_query('UPDATE `calculations` SET `priority` = 0 WHERE `queue` = ' + str(newq))
mysql_query('UPDATE `calculations` SET `leaf` = 1 WHERE `queue` = ' + str(newq))
