import os,subprocess,json

def readCOM(directory=None):
    if directory == None:
        directory = os.getcwd()
    template = dict()
    COMname = subprocess.Popen('ls -la | grep com | awk \'{print $9}\'',stdout=subprocess.PIPE,shell=True).communicate()[0].strip()
    COMfile = open(os.path.join(directory,COMname),'r')
    template['name'] = COMname.strip('.com') 
    i = 0
    
    for line in COMfile:
        if i >= 1:
            i += 1
        
        if line[0] == '%':
            temp = line[1:-1].strip().split('=')
            template[str(temp[0])] = temp[1] 
        
        if line[0] == '#':
            template['route']=line[1:-1].strip()
            i=1

        if i == 3:
            template['comment']=line.strip()

        if i == 5:
            cm = line.strip().split()
            template['charge'] = cm[0]
            template['multiplicity'] = cm[1]
            break
    COMfile.close()
    return template

def writeCOM(settings,directory=None):
    if directory == None:
        directory = os.getcwd()
    if not isinstance(settings,dict):
        settings = json.loads(settings)
    cfile = open(os.path.join(directory,settings['name'] + '.com'),'r')
    COMfile = cfile.readlines()
    routeindex = 0
    for i in range(0,len(COMfile)):
        if COMfile[i][0] == '%':
            temp = COMfile[i][1:-1].strip().split('=')
            COMfile[i] = '%' + temp[0] + '=' + str(settings[temp[0]]) + '\n'
        if COMfile[i][0] == '#':
            COMfile[i] = '#' + settings['route'] + '\n'
            routeindex = i

        if routeindex > 0:
            if routeindex == i - 2:
                COMfile[i] = settings['comment'] + '\n'

            if routeindex == i - 4:
                COMfile[i] = settings['charge'] + ' ' + settings['multiplicity'] + '\n'
    open(os.path.join(directory,settings['name'] + '.com'),'w').write(''.join(COMfile))
    cfile.close()
    return 0


