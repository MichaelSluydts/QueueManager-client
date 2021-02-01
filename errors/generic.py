from ..manage.calculation import updateResults,getResults
from ..communication.mysql import *
import importlib,json

def finderrors(calc):
    detectors = mysql_query('SELECT `id`,`detector`,`software` FROM `errors` WHERE `software` IN (\'' + calc['software'] + '\', \'any\') ORDER BY `priority` DESC')
    swdet = importlib.import_module('HighThroughput.errors.' + calc['software'] + 'detectors')
    generic = importlib.import_module('HighThroughput.errors.genericdetectors')
    errors = []
    calc['cerrors'] = []
    if not isinstance(detectors,list):
        detectors = [detectors]
    for det in detectors:
        #could join
        detector = mysql_query('SELECT `name` FROM `errorhandlers` WHERE `id` = ' + det['detector'])
        print('Checking for error ' + str(detector['name']))
        if det['software'] == 'any':
            func = getattr(generic,detector['name'])
        else:
            func = getattr(swdet,detector['name'])
        detected = func(calc)
        if detected:
            errors.append(det['id'])
            calc['cerrors'] = errors

    results = getResults(calc['parent'])
    if 'errors' not in results.keys():
        results['errors'] = 0

    print('DEBUG: number of errors' + str(len(errors)))
    if len(errors) > 0:
        err =','.join(errors)
        if 'errorfix' not in results.keys():
            results['errorfix'] = {}
        #else:
        #    results['errorfix'] = json.loads(results['errorfix'])
        
        if results['errors'] != err:
            results['errors'] = err
            results['errorfix'][err] = 0
            #results['errorfix'] = json.dumps(results['errorfix'])
            updateResults(results,calc['parent'])
        mainfuncs = importlib.import_module('HighThroughput.modules.' + calc['software'])
        abort = getattr(mainfuncs,'abort')
        return abort(calc)
    else:
        if 'errors' in results.keys():
            del results['errors']
        if 'errorfix' in results.keys():
            del results['errorfix']
        updateResults(results,calc['parent'])
        del calc['cerrors']
    return 0

def fixerrors(calc):
    results = getResults(calc['parent'])
    if 'errors' not in results.keys():
        return 0
    if 'errorfix' not in results.keys():
        results['errorfix'] = {}
    #else:
        #results['errorfix'] = json.loads(results['errorfix'])

    errors = results['errors'].split(',')
    for err in errors:
        fixflow = mysql_query('SELECT `flow` FROM `errors` WHERE `id` = ' + err)
        steps = fixflow['flow'].split(';')
        expanded = []
        for step in steps:
            curflow=step.split(':')
            if len(curflow) == 1:
                curflow.append(1)
            for i in range(0,int(curflow[1])):
                expanded.append(curflow[0])
        if err not in results['errorfix'].keys():
            results['errorfix'][err] = 0
        
        current = expanded[results['errorfix'][err] % len(expanded)]
        actions = current.split(',')
        swdet = importlib.import_module('HighThroughput.errors.' + calc['software'] + 'fixes')
        generic = importlib.import_module('HighThroughput.errors.genericfixes')
        for action in actions:
            fix = mysql_query('SELECT `name`,`description`, `software` FROM `errorhandlers` WHERE `id` = ' + action)
            if fix['software'] == 'any':
                func = getattr(generic,fix['name'])
            else:
                func = getattr(swdet,fix['name'])
            print('ERROR FIX: ' + fix['description'])
            func(calc)
        results['errorfix'][err] += 1
        #results['errorfix'] = json.dumps(results['errorfix'])
    results2 = getResults(calc['parent'])
    results2['errorfix'] = results['errorfix']
    print('This is the final errorfix update.')
    print(results2)
    updateResults(results2,calc['parent'])    
    return 0
