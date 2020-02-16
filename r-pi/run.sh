. /home/pi/fhoopz/venv/bin/activate
date >> /home/pi/fhoopz/daily_run.log
python3 /home/pi/fhoopz/daily_truth_update.py >> /home/pi/fhoopz/daily_run.log 2>&1
deactivate
