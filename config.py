# -*- coding: utf-8 -*-
import os,subprocess

vasp = 'vasp'

if os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
    vasp = 'vasp544ae-breniac-2016a_02-meta-rec-std'

scheduler = 'PBS'

if int(subprocess.Popen('printenv | grep SLURM | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0].decode()) > 0:
    scheduler = 'SLURM'
    walltime = subprocess.Popen('qstat -f | grep -A 15 $SLURM_JOB_ID | grep walltime | awk \'{print $3}\'',shell=True,stdout=subprocess.PIPE).communicate()[0].decode()
    if ':' in walltime:
        hours, minutes, seconds = tuple([int(x) for x in walltime.split(':')])
        os.environ['PBS_WALLTIME'] = str(hours*3600+minutes*60+seconds)

#group name to share queue directory
#test
#if os.getenv('VSC_INSTITUTE_CLUSTER') == 'breniac':
#    vasp = 'vasp_std'