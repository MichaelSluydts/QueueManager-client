from ..communication.mysql import mysql_query
import json,os
import HighThroughput.io.CIF as CIF
import time,pdb
calcid = 0;
sw = '';
stat = 0;
if os.getenv('PBS_JOBID') is not None:
    jobid = str(os.getenv('PBS_JOBID').split('.')[0]) 
else:
    jobid = '0'

def fetchgetstart(qid):
    global calcid, sw, stat
    i=0
    calc = ''
    while i < 10 and isinstance(calc,str):
        calc = mysql_query('FETCHGETSTART ' + str(qid) + ' ' + os.getenv('VSC_INSTITUTE_CLUSTER') + ' ' + str(os.getenv('PBS_JOBID')).split('.')[0] )
        if i > 0:
            time.sleep(60)
        i += 1
    
    if calc.get('id') is None:
        print('The database did not return any calculations from queue ' + str(qid) + ' at this time.')

    calcid = calc['id']
    sw = calc['software']
    stat = calc['stat']
    if not type(calc['results']) == dict:
        calc['results'] = json.loads(calc['results'])
    if not type(calc['settings']) == dict:
        calc['settings'] = json.loads(calc['settings'])
    return calc

def fetch(qid):
    return mysql_query('FETCHQ ' + str(qid))

def addgroup(group,queue,priority = '',settings = None,results = None, status = 0):
    rows = mysql_query('SELECT `id` FROM `newdata` WHERE `mgroup` = ' + str(group))
    materials = []
    for row in rows:
        materials.append(row['id'])
    batchadd(materials,queue,priority = '',settings = None,results = None, status = 0)

def batchadd(materials,queue,priority = '',settings = None,results = None, status = 0):
    global calcid, stat, sw
    #API conflict
    wftemplate = mysql_query('SELECT `priority`, `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' + str(queue) + ') AND `stat` = ' + str(status))
    if settings == None:
        settings = wftemplate['stemplate']

    if results == None:
        results = wftemplate['rtemplate']

    software = ''

    if isinstance(settings, dict):
        settings = json.dumps(settings)
        print('Be sure to update the software type.')
    elif str(settings).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(settings))
        settings = template['template']
        software = template['software']

    if isinstance(results, dict):
        results = json.dumps(results)
        print('Be sure to update the software type.')
    elif str(results).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(results))
        results = template['template']
        software = template['software']

    sw = software

    if priority == '':
        priority = wftemplate['priority']
    owner = mysql_query('');
    query = ''
    i=0
    for material in materials:
        if '10' not in material:
            print('skipped ' + material)
            continue
        query += 'INSERT INTO `calculations` (`queue`, `priority`, `owner`, `results`, `settings`, `software`, `file`, `stat`,`leaf`) VALUES (' + str(queue) + ', ' + str(priority) + ', ' + str(owner) + ',  \'' + results + '\', \'' + settings + '\', \'' + software + '\', ' + str(material) + ', ' + str(status) + ',1);'
        i+=1
        if i % 100 == 0:
            result = mysql_query(query);
            query = ''
    result = mysql_query(query);
    cid = result
    calcid = result
    queue = mysql_query('SELECT `id`, `name` FROM `queues` WHERE `id` = ' + str(queue))

    if(int(result) > 0):
        print('Added calculations to the ' + queue['name'] + ' queue (' + str(queue['id']) + ') as calculation ' + str(cid)  + '.')
    else:
        print('Adding calculations to the ' + queue['name']  + ' queue (' + str(queue['id']) + ') failed.')
    return cid

def add(material,queue,priority = '',settings = None,results = None, status = 0):
    global calcid, stat, sw
    #API conflict
    wftemplate = mysql_query('SELECT `priority`, `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' + str(queue) + ') AND `stat` = ' + str(status))
    if settings == None:
        settings = wftemplate['stemplate']

    if results == None:
        results = wftemplate['rtemplate']

    software = ''

    if isinstance(settings, dict):
        settings = json.dumps(settings)
        print('Be sure to update the software type.')
    elif str(settings).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(settings))
        settings = template['template']
        software = template['software']

    if isinstance(results, dict):
        results = json.dumps(results)
        print('Be sure to update the software type.')
    elif str(results).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(results))
        results = template['template']
        software = template['software']

    sw = software

    if priority == '':
        priority = wftemplate['priority']

    owner = mysql_query('');
    result = mysql_query('INSERT INTO `calculations` (`queue`, `priority`, `owner`, `results`, `settings`, `software`, `file`, `stat`,`leaf`) VALUES (' + str(queue) + ', ' + str(priority) + ', ' + str(owner) + ',  \'' + results + '\', \'' + settings + '\', \'' + software + '\', ' + str(material) + ', ' + str(status) + ',1)');
    oldcid = calcid
    cid = result
    calcid = result
    queue = mysql_query('SELECT `id`, `name` FROM `queues` WHERE `id` = ' + str(queue))

    if(int(result) > 0):
        mysql_query('UPDATE `calculations` SET `leaf` = 0 WHERE `id` = ' + str(oldcid))
        print('Added calculation for material ' + str(material) + ' (' + str(cid) + ') to the ' + queue['name'] + ' queue (' + str(queue['id']) + ') as calculation ' + str(cid)  + '.')
    else:
        print('Adding calculation for material ' + str(material) + ' to the ' + queue['name']  + ' queue (' + str(queue['id']) + ') failed.')
    return cid

def modify(params):
    query = 'UPDATE `calculations` SET '
    for key in params.keys():
        if key != 'id':
            query += '`' + key  + '` ='
            if isinstance(params[key],dict):
                query  += '\'' + json.dumps(params[key]).translate(str.maketrans({"'":  r"\'"})) + '\''
            elif not str(params[key]).isdigit():
                query += '\'' + str(params[key]).translate(str.maketrans({"'":  r"\'"})) + '\''
            else:
                query += str(params[key])
            query += ', '
    query = query[:-2] + ' WHERE `id` = ' + str(params['id'])
    #query = query.translate(str.maketrans({"'":  r"\'"}))
    result = int(bool(mysql_query(query)))
    if (result == 1):
        print('The calculation has been modified. Please verify.')
    elif (result == 0):
        print('Nothing to modify.')
    else:
        print('Help... Me...')
    return result

def getSettings(cid = None):
    if(cid == None):
        cid = calcid
    result = mysql_query('SELECT `settings` FROM `calculations` WHERE `id` = ' + str(cid))
    return json.loads(result['settings'])

def getResults(cid = None):
    if(cid == None):
        cid = calcid
    result = mysql_query('SELECT `results` FROM `calculations` WHERE `id` = ' + str(cid))
    return json.loads(result['results'])


def updateSettings(settings,cid = None):
    if(cid == None):
        cid = calcid

    if isinstance(settings, dict):
        settings = json.dumps(settings)
    elif str(settings).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(settings))
        settings = template['template']

    tempdict = {'id' : cid, 'settings': settings}
    return modify(tempdict)

def updateResults(results,cid = None):
    if(cid == None):
        cid = calcid

    if isinstance(results, dict):
        results = json.dumps(results)
    elif str(results).isdigit():
        template = mysql_query('SELECT * FROM `templates` WHERE `id` = ' + str(results))
        results = template['template']
    print('Updating results of calculation ' + str(cid) + '.')
    tempdict = {'id' : cid, 'results': results}
    return modify(tempdict)

def remove(cid):
    result = mysql_query('DELETE FROM `calculations` WHERE `id` = ' + str(cid))
    if (result == '1'):
        print('Calculation ' + str(cid) + ' has been removed.')
    else:
        print('Removing calculation ' + str(cid) + ' has failed.')

def get(cid):
    global calcid, sw, stat;

    material = mysql_query('SELECT `file` FROM `calculations` WHERE `id` = ' + str(cid))


    if isinstance(material, str):
        return material
    
    if(int(material['file']) < 10000000):
        table = 'data'
    else:
        table = 'newdata'

    result = mysql_query('SELECT * FROM `calculations` JOIN `' + table + '` ON (`calculations`.`file` = `' + table + '`.`file`) WHERE `calculations`.`id` = ' + str(cid))
    result['results'] = json.loads(result['results'])
    result['settings'] = json.loads(result['settings'])

    if not isinstance(result, str):
        calcid = cid
        sw = result['software']
        stat = result['stat']
    else:
        print('Retrieving calculation ' + str(cid) + ' failed.')
    return result

def start(cid = None):
    global stat,sw,calcid
    status = 0
    manual = True
    if cid == None:
        cid = calcid
        manual = False

    if(int(cid) > 0):
        calc = mysql_query('SELECT * FROM `calculations` WHERE `id` = ' + str(cid))
        if manual == False:
            status = stat
        else:
            status = calc['stat']
        #already = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `queue` = ' + calc['queue'] + ' AND `file` = ' + calc['file'] + ' AND `stat` IN (' + str(int(calc['stat'])+1) + ', ' + str(int(calc['stat'])+2) + ' AND `start` > DATE_SUB(NOW(), INTERVAL 1 HOUR))')
        already = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `parent` = ' + str(calc['id']))

        if int(status) % 2 != 0 or int(already['count']) > 0:
            return 0

        #restart = mysql_query('SELECT COUNT(`file`) AS `count` FROM `calculations` WHERE `queue` = ' + calc['queue'] + ' AND `file` = ' + calc['file'] + ' AND `stat` = ' + calc['stat'])
        # and restart['count'] == 1
        status = int(status) + 1
#using stat here as global feels a bit dodgy
        wftemplate = mysql_query('SELECT `priority`, `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' + str(calc['queue']) + ') AND `stat` = ' + str(status))
        if(int(wftemplate['rtemplate']) > 0):
            results =wftemplate['rtemplate']
        else:
            results = calc['results']

        if(int(wftemplate['stemplate']) > 0):
            settings = wftemplate['stemplate']
        else:
            settings = calc['settings']

        if isinstance(wftemplate,str):
            priority = calc['priority']
        else:
            priority = wftemplate['priority']
        sw=calc['software']
        add(calc['file'],calc['queue'],priority, settings, results, status)
        mysql_query('UPDATE `calculations` SET `parent` = ' + str(cid) + ' WHERE `id` = ' + str(calcid))
        cid = calcid
        stat = status
        return int(mysql_query('UPDATE `calculations` SET `start` = NOW(), `server` = \'' + str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + jobid + '\' WHERE `id` = ' + str(cid)));

def restart(cid = None, reset = False):
    global stat,calcid,jobid
    #problem with 0 case
    status = 0
    manual = True
    settings = ''
    results = ''
    if cid == None:
        cid = calcid
    calc = get(cid)
    stat = int(calc['stat'])
    if(int(cid) > 0):
        if stat % 2 != 0:
            stat = stat - 1
            rollback(stat,cid=cid)
            cid=calcid
            calc = get(cid)
            #return 1
        else:
            stat = stat - 2
            rollback(stat,cid=cid)
            cid = calcid
            calc = get(cid)
            #return 1
        #cid = calcid

        status = stat
        results = json.dumps(calc['results']).replace('\'','\\\'')
        settings = json.dumps(calc['settings'])
        if reset:
            wftemplate = mysql_query('SELECT `rtemplate`, `stemplate` FROM `workflows` WHERE `id` = (SELECT `workflow` FROM `queues` WHERE `id` = ' +     str(calc['queue']) + ') AND `stat` = ' + str(status))
            if(int(wftemplate['rtemplate']) > 0):
                template = mysql_query('SELECT `template` FROM `templates` WHERE `id` = ' + str(wftemplate['rtemplate']))
                results = template['template']

            if(int(wftemplate['stemplate']) > 0):
                template = mysql_query('SELECT `template` FROM `templates` WHERE `id` = ' + str(wftemplate['stemplate']))
                settings = template['template']
        print('UPDATE `calculations` SET `stat` = ' + str(status) + ', `start` = 0, `end` = 0, `server` = \'' + str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + jobid +     '\', `results` = \'' + results + '\', `settings` = \'' + settings + '\', `leaf` = 1 WHERE `id` = ' + str(cid))
    return int(mysql_query('UPDATE `calculations` SET `stat` = ' + str(status) + ', `start` = 0, `end` = 0, `server` = \'' + str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + jobid + '\', `results` = \'' + results + '\', `settings` = \'' + settings + '\', `leaf` = 1 WHERE `id` = ' + str(cid)));

def rollback(status, cid=None):
    global calcid, stat
    manual = True
    if cid != None:
        calcid = cid
    current = get(calcid)
    while int(current['stat']) > int(status) and not isinstance(current,str):
        oldcid = current['id']
        current = get(current['parent'])
        if isinstance(current,str):
            restart(oldcid)
            break
        else:
            mysql_query('DELETE FROM `calculations` WHERE `id` = ' + str(oldcid))
            calcid = current['id']
    modify({'id' : current['id'], 'leaf': 1})
    return 1

def showAll(qid):
    return mysql_query('SELECT * FROM `calculations` WHERE `queue` = ' + str(qid))

def end(cid = None):
    global stat
    status = 0
    manual = True
    if cid == None:
        cid = calcid
        manual = False
    if(int(cid) > 0):
        if manual == False:
            stat = int(stat) + 1
            status = stat
        else:
            status = mysql_query('SELECT `stat` FROM `calculations` WHERE `id` = ' + str(cid))
            status = int(status['stat'])+1
        output = {'VASP' : 'CONTCAR', 'Gaussian' : str(cid) + '.log'}
        CIFtext = ''
        if sw:
            if sw in output.keys():
                if os.path.isfile(output[sw]):
                    cif = CIF.read(output[sw],sw)
                    CIFtext = CIF.write('temp.cif',cif)
                    os.remove('temp.cif')
        return int(bool(mysql_query('UPDATE `calculations` SET `stat` = ' + str(status) + ', `end` = NOW(), `server` = \'' +str(os.getenv('VSC_INSTITUTE_CLUSTER')) + '\', `jobid` = \'' + str(os.getenv('PBS_JOBID')).split('.')[0] + '\', `cif` = \'' + CIFtext.replace('\'','\\\'') + '\' WHERE `id` = ' + str(cid))));
    else:
        return 0

def setPriority(priority,cid = None):
    if cid == None:
        cid = calcid

    if(str(priority).isdigit()):
      #  print('UPDATE `calculations` SET `priority` = ' + str(priority) + ' WHERE `id` = ' + str(cid)) 
        return mysql_query('UPDATE `calculations` SET `priority` = ' + str(priority) + ' WHERE `id` = ' + str(cid))
    else:
        print('Priorities are number, the higher the number the higher the priority')
    return 0
    
def setMultiplePriorities(priorities):
    priorities = priorities.sort_values(ascending=False,by='priority')
    query = ''
    for i,p in priorities.iterrows():
        query += 'UPDATE `calculations` SET `priority` = ' + str(p['priority']) + ' WHERE `id` = ' + str(p['id']) + ';\n'
    return mysql_query(query)
    
def getPriority(qid, stat):
    return mysql_query('SELECT `id` from `calculations` WHERE `stat` = '+str(stat)+' AND `queue` = ' + str(qid))
