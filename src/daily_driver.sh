#!/bin/bash

# assumes you've pip installed pandas and nba-api into venv, FWIW

source venv/bin/activate
python3 src/daily_csv.py
python3 src/player_totals_csv.py
python3 src/fscores_csv.py > data/reports/fgames.txt
python3 src/build_txt.py > data/reports/homepage.txt
python3 src/fplayers_txt.py > data/reports/fplayers.txt
python3 src/fteams_txt.py > data/reports/fteams.txt
deactivate

aws s3 sync data/ s3://fischerthings.com/fhoopz/ --acl public-read || exit 1
for id in `cat ~/fischerthings.ids`; do
  aws cloudfront create-invalidation --distribution-id $id --paths "/*";
done
