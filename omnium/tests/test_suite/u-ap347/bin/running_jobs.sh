#/usr/bin/env bash
JOB_IDS=`qstat -au $USER|grep $USER|awk '{print $1}'`
echo $JOB_IDS
