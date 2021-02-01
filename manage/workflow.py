from HighThroughput.communication.mysql import *
import os

#Could again make this global or a class
def get(workflow, stat = None):
    extra = ''
    if stat != None:
        extra = ' AND `stat` = ' + str(stat)
    return mysql_query('SELECT * FROM `workflows` WHERE `id`  = ' + str(workflow) + extra +  ' ORDER BY `stat`')

def showAll():
    return mysql_query('SELECT * FROM `workflows`')

def add(name,entries):
    owner = mysql_query('')
    newid = mysql_query('SELECT MAX(`id`) AS `newid` FROM `workflows` WHERE 1=1 OR 1=1')
    newid = int(newid['newid']) + 1
    for entry in entries:
        if('id' not in entry.keys()):
            entry['id'] = newid
        fields = '`owner`, '
        values = owner + ', '
        for key in entry.keys():
            fields += '`' + str(key)  + '`'
            if not str(entry[key]).isdigit():
                values += '\'' + str(entry[key]) + '\''
            else:
                values += str(entry[key])
            fields += ', '
            values += ', '
        result = mysql_query('INSERT INTO `workflows` (`name`, ' + str(fields[:-2])  + ') VALUES (\'' + str(name) + '\', ' + str(values[:-2]) + ')')
        #if(int(result) > 0):
        print('Added workflow entry ' + str(entry['stat']) + ' for workflow ' + str(name) + ' (' + str(entry['id']) + ')')
       # else:
        #    print 'Adding workflow failed (contact Michael)'
    return entry['id']

def modify(params):
    query = 'UPDATE `workflows` SET '
    for key in params.keys():
        if key != 'id' and key != 'stat':
            query += '`' + key  + '` ='
            if not params[key].isdigit():
                query += '\'' + params[key] + '\''
            else:
                query += params[key]
            query += ', '
    query = query[:-2] + ' WHERE `id` = ' + str(params['id']) + ' AND `stat` = ' + str(params['stat'])
    result = mysql_query(query)
    if (result == '1'):
        print('The workflow has been modified. Please verify.')
    else:
        print('Help... Me...')
    return int(result)
    
def remove(wid, stat):
    wid = str(wid)
    stat = str(stat)
    name = mysql_query('SELECT `name` FROM `workflows` WHERE `id` = ' + wid + ' LIMIT 1')
    result = mysql_query('DELETE FROM `workflows` WHERE `id` = ' + wid + ' AND `stat` = ' + stat)
    if (result == '1'):
        print('Status ' + stat + ' of the ' + name['name'] + '(' + wid + ') workflow has been removed.')
    else:
        print('Removing the ' + stat  + ' stat of ' + name['name'] + '(' + wid + ') has failed.')
    return int(result)

def removeAll(wid):
    wid = str(wid)
    name = mysql_query('SELECT `name` FROM `workflows` WHERE `id` = ' + wid + ' LIMIT 1')
    result = mysql_query('DELETE FROM `workflows` WHERE `id` = ' + wid)
    if (int(result) > 0):
        print('The ' + name['name'] + ' (' + wid + ') workflow has been removed.')
    else:
        print('Removing ' + name['name'] + ' (' + wid + ') has failed.')

def setPriority(priority,wid,stat):
    if(str(priority).isdigit()):
        return int(mysql_query('UPDATE `workflows` SET `priority` = ' + str(priority) + ' WHERE `id` = ' + str(wid) + ' AND `stat` = ' + str(stat)))
    else:
        print('Priorities are number, the higher the number the higher the priority')
        return 0
