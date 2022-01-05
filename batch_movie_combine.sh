#!/bin/bash --login
#$ -N emep_extraction            
#$ -cwd

# script for building daily movies, and combining these into one movie file 

module load apps/binapps/ffmpeg/4.1.3

start_date=20210101
days_to_process=120

if [[ -e file_list.txt ]] ; then rm file_list.txt ; fi

for i in $(seq 0 $days_to_process); do 

    #proc_date=$(date -j -v "+${i}d" -f "%Y%m%d" $start_date +%Y-%m-%d)
    proc_date=$(date -d "$start_date +${i} day" +"%Y-%m-%d" )

    ffmpeg -framerate 2 -i testfig2_${proc_date}T%02d.png -c:v libx264 -r 30 -pix_fmt yuv420p no2_movie_${proc_date}.mp4

    echo "file 'no2_movie_${proc_date}.mp4'" >> file_list.txt
    
done

ffmpeg -f concat -i file_list.txt -c copy out2.mp4
