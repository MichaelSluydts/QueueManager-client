import HighThroughput.manage
from HighThroughput.communication.mysql import mysql_query, owner
from time import sleep
import sys
def run():
    input('Welcome to the alpha test demo. This script will show you the main functionalities of the Queue Manager, once done please look inside the script to understand the various functions used. It is recommended to look through the case study in the manual beforehand. This script will reproduce what was shown there. \n\n To start please login to http://physics.epotentia.com/queue/ (only for the demo) then press any key to continue.')
    print('\n\nLogging in'),

    #Yes this is cheap, I know
    for i in range(1,4):
        sleep(1)
        sys.stdout.flush()
        print('.',)

    #These are deep level MySQL functions, you are discouraged from using them, but if you need to you can (ask me). All MySQL functions are supported, including statistical functions. The underlying library here tries to automatically limit your access to only your data. For this it does pattern recognition on your queries, very advanced queries may conflict with this. The owner variable is automatically set and contains your user id.
    name = mysql_query('SELECT `name` FROM `accounts` WHERE `id` = ' + owner)
    print('\n\n Welcome ' + name['name'] + ', are you ready to begin?')
    input()

    print('Great! We will start by setting up a settings and results template.')
    
    settings = {'Temperature' : 180, 'time' : 20}
    print('\n\nThe settings dictionary: ')
    print(settings)
    settingsid = HighThroughput.manage.template.add('Baking settings',settings,'VASP','settings')
    
    results = {'Crispiness' : '', 'Weight' : 0}
    print('\n\nThe results dictionary: ')
    print(results)
    resultsid = HighThroughput.manage.template.add('Baking results',results,'VASP','results')
    
    input('\n\nWe now have two templates ready to use in our workflow. Ready to add workflow?')
    
    name = 'Baking'
    button = ['Ingr. ready', 'Mixing', 'Mixed', 'Kneading', 'Kneaded', 'Rising', 'Risen', 'Baking', 'Finished']
    description = ['Ingredients ready', 'Mixing [server]', 'Mixed', 'Kneading [server]', 'Kneaded', 'Rising [server]', 'Risen', 'Baking [settings:Temperature]', 'Finished [results:weight]']
    buttonclass = ['warning','info','warning','info','warning','info','warning','info','success']
    entries = [{'stat' : i, 'stemplate' : settingsid, 'rtemplate' : resultsid, 'description' : description[i], 'buttonname' : button[i], 'buttonclass' : buttonclass[i], 'priority' : 1} for i in range(0,9)]
    print('')
    print(entries)
    print('')
    wid = HighThroughput.manage.workflow.add(name,entries)

    input('\n\nThe Baking workflow is ready. Ready to add queue?\n')
    
    #Doesn't conserve order, I should fix that... Can use string instead a:b,c:d,...
    #fields = {'ID' : 'id', 'Info' : 'text', 'Status' : 'stat', 'Start' : 'start', 'End' : 'end'}
    fields = 'ID:id,Info:text,Status:stat,Start:start,End:end'
    qid = HighThroughput.manage.queue.add('Jan de Bakker, Inc.', wid, fields)

    input('\n\nPlease go to the website and click Queues => View queues. Currently the website does not refresh automatically when new calculations are added, but you can just click the tab again. (Updates are autorefreshed (for quick updates you can set the refresh rate to 3000ms, going lower may be overkill.)\n\nIngredients would be added as materials normally, but to avoid unnecessary fake file creation we\'ll base our ingredients off a set of COD entries starting with FCC Al (CIF ID: 9012002). Ready to add calculations?\n')
    print('Adding calculations.\n')
    #add(material,queue,priority = 0,settings = None,results = None), templates are gotten from workflow by default
    calcs = []
    #I was going to edit this but then realized it's a bad idea to start renaming COD's materials for future usage yummy = ['Bread','Muffin','Cherry Pie','Pancake','Choccie Biscuit', 'Banana eclaire', 'Michel\'s cake','Cookies!','Sinterklaasventje','You get the point by now.']
    for i in range(0,10):
        calcs.append(HighThroughput.manage.calculation.add(9012002+i,qid,0))
        #fix the names
        #HighThroughput.manage.material.modify({'id' : , 'text' : yummy[i]})

    input('\n\nYou can now see the calculations on the website. Next is a demonstration of how calculations are managed. You should be able to follow this live on the website. Set your refresh rate to 3000 ms. Ready?')
    
    print('\n\nFetching a waiting calculation from the queue',)
    
    #Add a bit of drama, the real system is of course instant!
    for i in range(1,4):
        sleep(1)
        sys.stdout.flush()
        print('.',)

    fid = HighThroughput.manage.calculation.fetch(qid)
    print('\n\n Found calculation id ' + str(fid) + '. Get full calc info?\n\n')

    calculation = HighThroughput.manage.calculation.get(fid)

    print(calculation)

    input('\n\n Start calculation?')
   
    HighThroughput.manage.calculation.start()

    input('\n\n End calculation?')
    
    HighThroughput.manage.calculation.end()

    #We're moving the the calculation back to before the last active status so 1 or 2 steps, if you want to rollback further please use the rollback function (calculations beyond that status will be deleted!)
    input('\n\n Now if something went wrong... Restart calculation?')

    HighThroughput.manage.calculation.restart()
    
    input('\n\n Up the pace? Keep in mind each blue workflow is a new \'calculation\' and you\'ll have to manually click the queue currently (will fix sometime).')
    for i in range(0,20):
        fid = HighThroughput.manage.calculation.fetch(qid)
        calculation = HighThroughput.manage.calculation.get(fid)
        HighThroughput.manage.calculation.start()
        print('Starting calculation ' + str(HighThroughput.manage.calculation.calcid) + ' (status ' + str(HighThroughput.manage.calculation.stat) + ').')
        HighThroughput.manage.calculation.end()
        
        #Store the results, based on the template, can be put in the workflow description with [results:weight] etc, settings is similarly accessible.
        HighThroughput.manage.calculation.updateResults({'weight': (i+1)*50, 'Crispiness' : 'Just right'})
        
        print('Ending calculation ' + str(HighThroughput.manage.calculation.calcid) + ' (status ' + str(HighThroughput.manage.calculation.stat) + ').')
    
    input('\n\nContinuing will clean up everything added during this demo.')
    
    
    HighThroughput.manage.queue.remove(qid)
    HighThroughput.manage.workflow.removeAll(wid)
    HighThroughput.manage.template.remove(settingsid)
    HighThroughput.manage.template.remove(resultsid)
