. /home/pi/fhoopz/venv/bin/activate
date >> /home/pi/fhoopz/daily_run.log
python3 /home/pi/fhoopz/daily_truth_update.py >> /home/pi/fhoopz/daily_run.log 2>&1
python3 /home/pi/fhoopz/build_txt.py >> /home/pi/fhoopz/daily_run.log 2>&1
deactivate

for id in `cat /home/pi/fhoopz/ef-codes.cloudfront.ids`; do
  aws cloudfront create-invalidation --distribution-id $id --paths "/*";
done
