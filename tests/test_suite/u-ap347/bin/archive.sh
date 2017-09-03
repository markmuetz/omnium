#!/usr/bin/env bash
set -x
mkdir -p $ARCHIVE_DIR
rsync -av $CYLC_SUITE_RUN_DIR $ARCHIVE_DIR
