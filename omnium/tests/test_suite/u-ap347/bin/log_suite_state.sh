#!/usr/bin/env bash
echo "Logging suite state"

cd $HOME/roses/$SUITE

DATE=`date +"%Y%m%dT%H%M%SZ"`
LOG_DIR=$HOME/suite_log/$SUITE/
LOG_FILE=$LOG_DIR/run_log.txt

DETAILED_LOG_DIR=$LOG_DIR/${DATE}
DETAILED_LOG_FILE=$DETAILED_LOG_DIR/detailed_log.txt

mkdir -p $LOG_DIR
mkdir -p $DETAILED_LOG_DIR

echo "$DATE: Running $SUITE" >> $LOG_FILE
echo `pwd` >> $DETAILED_LOG_FILE

cp rose-suite.conf $DETAILED_LOG_DIR

fcm info >> $DETAILED_LOG_DIR/fcm_info.txt
FCM_STATUS=`fcm status`
echo $FCM_STATUS >> $DETAILED_LOG_DIR/fcm_status.txt

fcm diff >> $DETAILED_LOG_DIR/fcm.diff
fcm info|grep "^Last Changed Rev"|awk '{print $4}' >> $DETAILED_LOG_DIR/fcm_rev.txt

cd archer_analysis
../bin/git-info.sh >> $DETAILED_LOG_DIR/archer_analysis_git_info.txt
git rev-parse HEAD >> $DETAILED_LOG_DIR/archer_analysis_git_rev.txt

GIT_STATUS=`git status`
GIT_STATUS_PORCELAIN=`git status --porcelain`
echo $GIT_STATUS >> $DETAILED_LOG_DIR/archer_analysis_git_status.txt

echo $PRODUCTION >> $DETAILED_LOG_FILE
echo $GIT_STATUS >> $DETAILED_LOG_FILE
echo $GIT_STATUS_PORCELAIN >> $DETAILED_LOG_FILE
echo $FCM_STATUS >> $DETAILED_LOG_FILE

if [  "$PRODUCTION" == "True" ]; then
    echo "Production run" >> $DETAILED_LOG_FILE
    if [ -n "$FCM_STATUS" ]; then
	echo "fcm status not empty; suite has uncommitted changes: aborting" >> $DETAILED_LOG_FILE
	exit 1
    fi
fi

git diff >> $DETAILED_LOG_DIR/archer_analysis_git.diff
cd ..
