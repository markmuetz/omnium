#!/bin/bash

#
# Displays information about the current working copy of a Git checkout
# and how it relates back to the remote branch it is tracking (if there is one)
#
# Jeff Caddel <jcaddel at yahoo dot com>
#

function check_git_dir {
  local IS_GIT_DIR=$(git rev-parse --is-inside-work-tree)
  if [ ! "$IS_GIT_DIR" == "true" ]; then
    exit 1
  fi
}

function get_last_modified {
  echo -e -n "$(git show --format="%ci %cr" $1 | head -n 1 | cut -d ' ' -f4-6)"
}

check_git_dir

REMOTE=$1
if [ "$REMOTE" == "" ]; then
  REMOTE=origin
fi

if [ "$(git remote | grep $REMOTE)" == "" ]; then
  echo "remote '$REMOTE' does not exist"
  exit 1
fi

git remote update $REMOTE > /dev/null 2>&1

REMOTE_URL=$(git config --get remote.$REMOTE.url)
BRANCH=$(git rev-parse --abbrev-ref HEAD)

LAST_REMOTE_COMMIT=""
REMOTE_LAST_MODIFIED=""
REMOTE_BRANCH_EXISTS=false
if [ ! "$(git branch -r  | grep $GROUP/$BRANCH)" == "" ]; then
  REMOTE_BRANCH_EXISTS=true
  LAST_REMOTE_COMMIT=$(git rev-parse $REMOTE/$BRANCH)
  REMOTE_LAST_MODIFIED=$(get_last_modified $REMOTE/$BRANCH)
fi

LAST_LOCAL_COMMIT=$(git --no-pager log --max-count=1 | head -n1 | cut -d ' ' -f2)
LOCAL_LAST_MODIFIED=$(get_last_modified $BRANCH)

INSYNC=false
if [ "$LAST_LOCAL_COMMIT" == "$LAST_REMOTE_COMMIT" ]; then
  INSYNC=true
fi

while [ ! -d .git ] && [ ! `pwd` = "/" ]; do cd ..; done
WORKING_COPY_ROOT_PATH=$(pwd)

echo "Working Copy Root Path: $WORKING_COPY_ROOT_PATH"
echo "                Remote: $REMOTE"
echo "            Remote URL: $REMOTE_URL"
echo "                Branch: $BRANCH"
echo "     Last Local Commit: $LAST_LOCAL_COMMIT ($LOCAL_LAST_MODIFIED)"
if [ "$REMOTE_BRANCH_EXISTS" == "true" ]; then
  echo "    Last Remote Commit: $LAST_REMOTE_COMMIT ($REMOTE_LAST_MODIFIED)"
  echo "          Synchronized: $INSYNC"
else
  echo "    Last Remote Commit: -- no remote branch --"
  echo "          Synchronized: -- no remote branch --"
fi