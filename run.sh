#!/bin/sh

source /Users/kathyems/Dropbox/git/pcc-tee-times/.venv/bin/activate
set -o allexport
source /Users/kathyems/Dropbox/git/pcc-tee-times/.env
set +o allexport
python3 /Users/kathyems/Dropbox/git/pcc-tee-times/main.py $1 $2 $3 $4 $5 $6 $7
