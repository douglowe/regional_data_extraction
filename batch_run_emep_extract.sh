#!/bin/bash --login
#$ -N emep_extraction            
#$ -cwd


source ~/bin/conda_activate.sh 
conda activate emep_extract

WRF_FILE='../../WRF_Man/2021/wrfout_d02_2021-01-07_00:00:00'


pull_stat_data(){
INPUT_ARGS="--wrf_file ${WRF_FILE} --emep_file ${EMEP_FILE} --data_name ${DATA_VAR}"
STAT_ARGS="--stat_data --file_name ${STAT_FILE}"
PLOT_ARGS="--no_plot_data"
python gm_extract_data.py ${INPUT_ARGS} ${STAT_ARGS} ${PLOT_ARGS}
}


EMEP_FILE='../../EMEP_Man/Base_hourInst_JanFeb2021.nc'
DATA_VAR='SURF_ug_PM25'
STAT_FILE='PM25_stat_data_JanFeb2021.csv'
pull_stat_data


EMEP_FILE='../../EMEP_Man/Base_hourInst_MarApr2021.nc'
DATA_VAR='SURF_ug_PM25'
STAT_FILE='PM25_stat_data_MarApr2021.csv'
pull_stat_data





echo "finished extraction task"
