#!/bin/bash
walltime=$[$2-1]':59:00'

if [ $2 -gt 72 ]; then
    queue='special'
elif [ $2 -gt 12 ]; then
        queue='long'
elif [ $2 -eq 1 ]; then
        queue='debug'
else
        queue='short'
fi
jobs='scripts'
if [ $VSC_INSTITUTE_CLUSTER == 'muk' ]; then
    if [ $2 -eq 1 ]; then
        queue='debug'
    else
        queue='batch'
    fi
    cd $pscratch/queues/$1/LOGFILES
elif [ $VSC_INSTITUTE_CLUSTER == 'breniac' ]; then
   if [ $2 -gt 72 ]; then
       queue='q7d'
   elif [ $2 -gt 24 ]; then
       queue='q72h'
   elif [ $2 -gt 1 ]; then
       queue='q24h'
   else
       queue='q1h'
   fi
   cd $VSC_SCRATCH/queues/$1/LOGFILES
else
    cd /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/
fi

if [ $VSC_INSTITUTE_CLUSTER == 'breniac' ]; then
    VASP='5.4.1-intel-2016a-VTST'
    python='2.7.11-intel-2016a'
else
    VASP='5.4.1.05Feb16-intel-2016b-mt-vaspsol-20150914-O2-patched-03082016'
    python='2.7.12-intel-2016b'
fi


if [ "$4" -lt "8" ] && [ "$2" -lt "72" ]; then
    small='_S'
    version='1'
else
    small=''
    version='0'
fi

space='_'

dir=`pwd`
cat > ${VSC_INSTITUTE_CLUSTER}.sh << !
#!/bin/bash
#PBS -N Q$1$space$2$space$3$space$4$small

#PBS -A lt1_2017-61

#PBS -m a

#PBS -q $queue

#PBS -l walltime=$walltime

#PBS -l nodes=$3:ppn=28

#PBS -l pmem=4gb

#PBS -lqos=debugging

ulimit -s unlimited

cd /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/

module load HighThroughput/michiel
source activate breniac
python /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/reset.py
python /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/backtest.py
source deactivate
exit 0
!

qsub ${VSC_INSTITUTE_CLUSTER}.sh
