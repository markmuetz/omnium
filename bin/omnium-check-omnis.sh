#!/bin/bash
for d in */ ; do
    if [[ $d = _* ]]; then
	continue
    fi
    >&2 echo "$d"
    cd $d
    omni print-config
    omni print-nodes
    omni print-config computers $1 remote
    ret_code=$?
    if [ $ret_code == 0 ]; then
	>&2 echo "syncing metadata"
	omni sync -m
    else
        omni gen-nodes --regen
    fi
    cd ..
done
