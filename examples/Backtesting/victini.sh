#!/bin/bash
#PBS -N Q254_12_1_36


#PBS -m a


#PBS -l walltime=11:59:00

#PBS -l nodes=1:ppn=9


ulimit -s unlimited


module load HighThroughput/michiel
source activate breniac

cd /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting

python /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/reset.py
python /user/data/gent/gvo000/gvo00003/shared/bin/HT/edge/HighThroughput/examples/Backtesting/backtest.py

exit 0
