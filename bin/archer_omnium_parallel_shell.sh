#!/bin/bash
echo $@

source $WORK/load_p3c_iris.sh

export HOME=$WORK
export PATH=$PATH:$WORK/.local/bin/:$WORK/bin
export CYLC_CONTROL=True
export OMNIUM_BASE_SUITE_DIR=/work/n02/n02/mmuetz/cylc-run/
export OMNIUM_ANALYSIS_PKGS=scaffold

aprun -n 10 -N 10 omnium $@
