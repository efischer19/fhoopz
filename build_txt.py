# standard imports
import boto3
from datetime import datetime, date, timedelta
from io import StringIO
from os import path

# from layers
import pandas as pd

# common setup
irl_data_path = 's3://www.eric-fischer.codes/fhoopz/data/irl/'
schedule_f = pd.read_csv(irl_data_path + 'schedule/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t')
standings_f = pd.read_csv(irl_data_path + 'standings/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t', index_col='TEAM_ID')
today_txt = StringIO()

# the IRL standings
today_txt.write("Eastern Conference Standings:\n")
east = standings_f.loc[standings_f['CONFERENCE'] == 'East']
east = east[['TEAM', 'W', 'L']]
east['TEAM'] = east['TEAM'].str.pad(13)
today_txt.write(east[:6].to_string(index=False))
today_txt.write("\n")
today_txt.write('-'*25)
today_txt.write("\n")
today_txt.write(east[6:10].to_string(index=False, header=False))
today_txt.write("\n")
today_txt.write('*'*25)
today_txt.write("\n")
today_txt.write(east[10:].to_string(index=False, header=False))
today_txt.write("\n\n")

today_txt.write("Western Conference Standings:\n")
west = standings_f.loc[standings_f['CONFERENCE'] == 'West']
west = west[['TEAM', 'W', 'L']]
west['TEAM'] = west['TEAM'].str.pad(13)
today_txt.write(west[:6].to_string(index=False))
today_txt.write("\n")
today_txt.write('-'*25)
today_txt.write("\n")
today_txt.write(west[6:10].to_string(index=False, header=False))
today_txt.write("\n")
today_txt.write('*'*25)
today_txt.write("\n")
today_txt.write(west[10:].to_string(index=False, header=False))
today_txt.write("\n\n")

# TODO: add game results from yesterday?

# top fantasy performers
__disabling_this_because_not_doing_fantasy = """
date_str = (date.today() - timedelta(1)).strftime("%Y-%m-%d")
yesterday_df = pd.read_csv(path.join(irl_data_path, 'game_logs', date_str + ".csv"), sep='\t')
fvals = {
  "PTS": 1,
  "REB": 1.25,
  "AST": 1.5,
  "STL": 2,
  "BLK": 3,
  "TOV": -1.5
}
today_txt.write("\nTop performers from yesterday\nFPTS  | PTS/REB/AST/STL/BLK/TOV\n")
p_strings = []
for p_row in yesterday_df.iterrows():
    ftotal = 0
    for stat, fval in fvals.items():
        ftotal += (p_row[1][stat] * fval)
    if p_row[1]['WL'] == 'W':
        ftotal += 5
    if ftotal >= 25:
        linestring = ""
        for k in ['PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV']:
            linestring += "{}/".format(p_row[1][k])
        namestring = "{} {}".format(p_row[1]['MATCHUP'][:3], p_row[1]['PLAYER_NAME'])
        p_strings.append("{} | {:13} - {}\n".format(str(ftotal).ljust(5), linestring[:-1], namestring))

for player_line in sorted(p_strings, reverse=True):
    today_txt.write(player_line)
"""

#then, today's games (start time, away @ home (team names), national tv)
today_txt.write("\nToday's games:\n")
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

today_txt.write("\nGenerated at {}".format(datetime.now().isoformat()))

s3_resource = boto3.resource("s3")
response = s3_resource.Object('www.eric-fischer.codes', 'nba.txt').put(
    ACL='public-read',
    Body=today_txt.getvalue(),
    ContentDisposition='inline',
    ContentType='text/plain'
)
