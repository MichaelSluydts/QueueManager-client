from HighThroughput.communication.mysql import *
import os

def get(qid):
    queue = mysql_query('SELECT * FROM `queues` WHERE `id` = ' + str(qid))
    return queue

def showAll():
    return mysql_query('SELECT * FROM `queues`')

def add(name,workflow='1',fields='ID:id,Info:text,Material ID:file,Status:stat,Jobid:jobid,Start:start,End:end',directory=os.getcwd()):
    owner = mysql_query('')
    dbfield = ''
    if (isinstance(fields, dict)):
        for field in fields.keys():
            dbfield += field + ':' + fields[field] + ','
        dbfield = dbfield[:-1]
    else:
        dbfield = fields
    result = mysql_query('INSERT INTO `queues` (`name`, `owner`, `dir`, `fields`, `workflow`) VALUES (\'' + str(name)  + '\', ' + str(owner) + ', \'' + str(directory) + '\',\'' + str(dbfield)  + '\', ' + str(workflow) + ')')
    qid = result
    if(int(result) > 0):
        print('The ' + name + ' queue has been added and assigned id ' + str(qid))
    else:
        print('Adding queue failed (contact Michael)')
    return qid

def modify(params):
    query = 'UPDATE `queues` SET '
    for key in params.keys():
        if key != 'id':
            query += '`' + key  + '` ='
            if not str(params[key]).isdigit():
                query += '\'' + str(params[key]) + '\''
            else:
                query += str(params[key])
            query += ', '
    query = query[:-2] + ' WHERE `id` = ' + str(params['id'])
    result = mysql_query(query)
    if (result == '1'):
        print('The queue has been modified. Please verify.')
    else:
        print('Help... Me...')
    
def remove(qid):
    name = mysql_query('SELECT `name` FROM `queues` WHERE `id` = ' + str(qid))
    result = mysql_query('DELETE FROM `queues` WHERE `id` = ' + str(qid))
    result2 = mysql_query('DELETE FROM `calculations` WHERE `queue` = ' + str(qid))
    if (result == '1'):
        print('The ' + name['name'] + '(' + str(qid) + ') queue has been removed.')
    else:
        print('Removing the ' + name['name'] + '(' + str(qid) + ') has failed.')
    return int(result)

