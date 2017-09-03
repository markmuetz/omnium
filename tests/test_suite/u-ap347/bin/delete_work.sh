#!/usr/bin/env bash
set -x
cd $CYLC_SUITE_RUN_DIR/share/data/
rm -rf history
cd $CYLC_SUITE_RUN_DIR
rm -rf work
