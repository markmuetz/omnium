#/usr/bin/env bash
#set -x
JOB_ID=$1
START_TIMESTEPS=$2
TOTAL_TIMESTEPS=$3
CYCLE=$4

JOB_NAME=`qstat -Jf ${JOB_ID}|grep Job_Name|awk '{print $3}'`
echo "Job name: $JOB_NAME"

TIMESTEPS=`find ../work -wholename "*$CYCLE*${JOB_NAME}*atmos.fort6.pe000*" |xargs tail -n3|head -n1|awk '{print $6}'`
WALLTIME=`qstat -Jf $JOB_ID|grep resources_used.walltime|awk '{print $3}'| awk -F: '{ print ($1 * 3600) + ($2 * 60) + $3 }'`

echo "Timesteps: $TIMESTEPS"
echo "Start timesteps: $START_TIMESTEPS"
echo "Total timesteps: $TOTAL_TIMESTEPS"
echo "Walltime: ${WALLTIME}s"

PERCENT_DONE=`echo "$TIMESTEPS $START_TIMESTEPS $TOTAL_TIMESTEPS"|awk '{print 100.*($1-$2)/$3}'`
TIME_SO_FAR=`echo $WALLTIME|awk '{print 1.*$1/3600}'`
PRED_TIME=`echo "$TOTAL_TIMESTEPS $TIMESTEPS $START_TIMESTEPS $WALLTIME"|awk '{print 1.*$1/($2-$3)*$4/3600}'`
PRED_TIME_SEC=`echo "$TOTAL_TIMESTEPS $TIMESTEPS $START_TIMESTEPS $WALLTIME"|awk '{print 1.*$1/($2-$3)*$4}'`
TIME_TO_GO=`echo "$PRED_TIME_SEC $WALLTIME"|awk '{print $1 - $2}'`

echo "Percent done: ${PERCENT_DONE}%"
echo "Time so far: ${TIME_SO_FAR}h"
echo "Predicted time: ${PRED_TIME}h"
START_TIME=`date -d "${WALLTIME%%.*} seconds ago"`
END_TIME=`date -d "${TIME_TO_GO%%.*} seconds"`
NOW=`date`
echo "Start time: ${START_TIME}"
echo "Time now: ${NOW}"
echo "End time: ${END_TIME}"
