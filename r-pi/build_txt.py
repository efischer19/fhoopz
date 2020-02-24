# standard imports
import boto3
from datetime import datetime, date, timedelta
from io import StringIO

# from layers
import pandas as pd

# common setup
irl_data_path = 's3://www.eric-fischer.codes/fhoopz/data/irl/'
schedule_f = pd.read_csv(irl_data_path + 'schedule/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t')
standings_f = pd.read_csv(irl_data_path + 'standings/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t', index_col='TEAM_ID')
today_txt = StringIO()

# TODO: add game results from yesterday?

# TODO: individual game logs from yesterday
# unsure how relevant these are w/o fantasy as the main focus?
"""
print()
print("Top performers from yesterday:")
date_str = (date.today() - timedelta(1)).strftime("%Y-%m-%d")
yesterday_df = pd.read_csv(path.join(irl_data_path, 'game_logs', date_str + ".csv"), index_col='PLAYER_ID')
fvals = {
  "PTS": 1,
  "REB": 1.25,
  "AST": 1.5,
  "STL": 2.5,
  "BLK": 2.5,
  "TOV": -1
}
result_strings = {}
for tid, roster in froster.items():
    for pid in roster:
        try:
            g_row = yesterday_df.loc[pid]
            ftotal = sum([
                g_row[stat]*fvals[stat]
                for stat in fvals
            ])
            fstr = '{:21} ({:^11}): '.format(g_row['PLAYER_NAME'], g_row['MATCHUP'])
            for stat in fvals:
                fstr += "{:2} {}, ".format(g_row[stat], stat)
        except KeyError:
            continue  # every player does not play every day, this is fine
"""

# the IRL standings
today_txt.write("Eastern Conference Standings:\n")
east = standings_f.loc[standings_f['CONFERENCE'] == 'East']
east = east[['TEAM', 'W', 'L']]
east['TEAM'] = east['TEAM'].str.pad(13)
today_txt.write(east[:8].to_string(index=False))
today_txt.write("\n")
today_txt.write('*'*25)
today_txt.write("\n")
today_txt.write(east[8:].to_string(index=False, header=False))
today_txt.write("\n\n")

today_txt.write("Western Conference Standings:\n")
west = standings_f.loc[standings_f['CONFERENCE'] == 'West']
west = west[['TEAM', 'W', 'L']]
west['TEAM'] = west['TEAM'].str.pad(13)
today_txt.write(west[:8].to_string(index=False))
today_txt.write("\n")
today_txt.write('*'*25)
today_txt.write("\n")
today_txt.write(west[8:].to_string(index=False, header=False))
today_txt.write("\n\n")


#then, today's games (start time, away @ home (team names), national tv)
today_txt.write("Today's games:\n")
for gid, row in schedule_f.iterrows():
    tv_str = ""
    if pd.notna(row['NATL_TV']):
        tv_str = ' ({})'.format(row['NATL_TV'])
    today_txt.write('{:13} @ {:13} {:>11}{}\n'.format(
        standings_f.loc[row['AWAY_ID']]['TEAM'],
        standings_f.loc[row['HOME_ID']]['TEAM'],
        row['START_TIME'],
        tv_str
    ))
today_txt.write("\n\n")

today_txt.write("\nGenerated at {}".format(datetime.now().isoformat()))

s3_resource = boto3.resource("s3")
response = s3_resource.Object('www.eric-fischer.codes', 'nba.txt').put(
    ACL='public-read',
    Body=today_txt.getvalue(),
    ContentDisposition='inline',
    ContentType='text/plain'
)
