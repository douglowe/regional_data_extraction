#!/bin/bash --login
#$ -N emep_extraction            
#$ -cwd


source ~/bin/conda_activate.sh 
conda activate emep_extract

WRF_FILE='../../WRF_Man/2021/wrfout_d02_2021-01-07_00:00:00'


plot_model_data(){
INPUT_ARGS="--wrf_file ${WRF_FILE} --emep_file ${EMEP_FILE} --data_name ${DATA_VAR}"
STAT_ARGS="--no_stat_data"
PLOT_ARGS="--plot_data --figure_string ${FIG_STRING} --data_label ${DATA_LABEL} --data_unit ${DATA_UNIT} --data_min ${DATA_MIN} --data_max ${DATA_MAX} --data_levels ${DATA_LEVELS}"
python gm_extract_data.py ${INPUT_ARGS} ${STAT_ARGS} ${PLOT_ARGS}
}


EMEP_FILE='../../EMEP_Man/Base_hourInst_JanFeb2021.nc'
DATA_VAR='SURF_ug_PM25'
DATA_LABEL='PM2.5'
DATA_UNIT='ug/m3'
FIG_STRING='pm25'
DATA_MIN='0'
DATA_MAX='80'
DATA_LEVELS='41'
plot_model_data


EMEP_FILE='../../EMEP_Man/Base_hourInst_MarApr2021.nc'
DATA_VAR='SURF_ug_PM25'
DATA_LABEL='PM2.5'
DATA_UNIT='ug/m3'
FIG_STRING='pm25'
DATA_MIN='0'
DATA_MAX='80'
DATA_LEVELS='41'
plot_model_data



echo "finished plotting task"
