#!/bin/bash

source ~/fhoopz/venv/bin/activate
python3 ~/fhoopz/daily_truth_update.py
python3 ~/fhoopz/build_txt.py
deactivate

for id in `cat ~/fhoopz/ef-codes.cloudfront.ids`; do
  aws cloudfront create-invalidation --distribution-id $id --paths "/*";
done
