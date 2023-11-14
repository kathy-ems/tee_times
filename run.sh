#!/bin/sh

source /Users/kathyle/git-local/personal/pcc-tee-times/.venv/bin/activate
set -o allexport
source /Users/kathyle/git-local/personal/pcc-tee-times/.env
set +o allexport
python3 /Users/kathyle/git-local/personal/pcc-tee-times/main.py $1 $2 $3 $4 $5 $6 $7
