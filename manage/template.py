from ..communication.mysql import *
import json

#Could add global or make class as well.

def add(name,value,software,ttype):
    result = mysql_query('INSERT INTO `templates` (`software`, `name`, `type`, `template`, `owner`) VALUES (\'' + str(software) + '\', \'' + str(name) + '\', \'' + str(ttype) + '\', \'' + json.dumps(value) + '\', ' + str(owner) + ')')
    tid = result 
    if(int(result) > 0):
        print('Template ' + str(name) + ' (' + str(tid) + ') has been succesfully added.')
    else:
        print('Adding template ' + str(name) + ' has failed.')
    return tid

def get(tid):
    template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(tid))
    return json.loads(template['template'])

def modify(params):
#should add check for id
    query = 'UPDATE `templates` SET '
    for key in params.keys():
        if key != 'id':
            query += '`' + key  + '` ='
            if key == 'template':
                query += '\'' + json.dumps(params[key]) + '\''
            elif not str(params[key]).isdigit():
                query += '\'' + params[key] + '\''
            else:
                query += str(params[key])
            query += ', '
    query = query[:-2] + ' WHERE `id` = ' + str(params['id'])
    result = mysql_query(query)
    
    if (result == '1'):
        print('The template has been modified. Please verify.')
    else:
        print('Help... Me...')

    return int(result)

def remove(tid):
    name = mysql_query('SELECT `name` FROM `templates` WHERE `id` = ' + str(tid))
    result = mysql_query('DELETE FROM `templates` WHERE `id` = ' + str(tid))
    if (result == '1'):
        print('The ' + name['name'] + ' (' + str(tid) + ') template has been removed.')
    else:
        print('Removing the ' + name['name'] + ' (' + str(tid) + ') has failed.')

    return int(result)
