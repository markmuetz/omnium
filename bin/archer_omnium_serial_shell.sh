#!/bin/bash
echo $@

source $WORK/.anaconda3_setup.sh 
source activate $WORK/conda/envs/iris36

export HOME=$WORK
export PATH=$PATH:$WORK/.local/bin/:$WORK/bin
export CYLC_CONTROL=True
export OMNIUM_BASE_SUITE_DIR=/work/n02/n02/mmuetz/cylc-run/
export OMNIUM_ANALYSIS_PKGS=scaffold

omnium $@
