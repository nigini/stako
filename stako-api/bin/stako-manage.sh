#!/bin/bash

LOG_FILE="/var/log/gunicorn/all.log"

#RESTART SERVER
killall gunicorn3
now=$(date +"%F_%T")
mv $LOG_FILE "${LOG_FILE}.${now}.bkp"
gunicorn3 --workers=3 stako.api.api:app --bind=0.0.0.0:8000 --chdir=/root/stako/stako-api/ 2>&1 | tee $LOG_FILE &
