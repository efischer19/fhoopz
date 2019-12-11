from datetime import date, timedelta
from decimal import Decimal
import json
from os import path
import pandas as pd

# inputs: league-specific files at data/fantasy/settings (rosters.json, scoring.json)
# other inputs: IRL data from data/irl

basepath = path.dirname(path.dirname(path.abspath(__file__)))
f_data_path = path.join(basepath, 'data', 'fantasy')
irl_data_path = path.join(basepath, 'data', 'irl')

#fteam standings at the top, just showing total points and current rosters
fteam_f = pd.read_csv(path.join(f_data_path, 'stats', 'fteams.csv'))
fplayer_f = pd.read_csv(path.join(f_data_path, 'stats', 'players.csv'), index_col='PLAYER_ID')
froster = {}
with open(path.join(f_data_path, 'settings', 'latest_roster.csv'), 'r') as f:
    froster = json.load(f)

print("Current fantasy standings and rosters:")
count = 1
for tid, row in fteam_f.iterrows():
    roster_str = ""
    for pid in froster[str(tid)]:
        fp = fplayer_f.loc[pid]
        roster_str += '{}, '.format(fp['PLAYER_NAME'])
    print('#{:2} {:<22}{:8.2f} | {}'.format(count, row['TEAM_NAME'], row['FPT'], roster_str[:-2]))
    count += 1

#then, game logs from yesterday
print()
print("Fantasy relevant lines from yesterday:")
fvals = {}
with open(path.join(f_data_path, "settings", "scoring.json"), "r") as rfile:
    fvals = json.load(rfile)
date_str = (date.today() - timedelta(1)).strftime("%Y-%m-%d")
yesterday_df = pd.read_csv(path.join(irl_data_path, 'game_logs', date_str + ".csv"), index_col='PLAYER_ID')
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
            print(fstr + "{:6.2f} FPTS".format(ftotal))
        except KeyError:
            continue  # every player does not play every day, this is fine

#then, today's games (start time, away @ home (team names), national tv)
fgame_f = pd.read_csv(path.join(irl_data_path, 'schedule', date.today().strftime('%Y-%m-%d.csv')))
fstandings_f = pd.read_csv(path.join(irl_data_path, 'standings', date.today().strftime('%Y-%m-%d.csv')), index_col='TEAM_ID')

print()
print("Today's games:")
for gid, row in fgame_f.iterrows():
    tv_str = ""
    if pd.notna(row['NATL_TV']):
        tv_str = ' ({})'.format(row['NATL_TV'])
    print('{:13} @ {:13} {:>11}{}'.format(
        fstandings_f.loc[row['AWAY_ID']]['TEAM'],
        fstandings_f.loc[row['HOME_ID']]['TEAM'],
        row['START_TIME'],
        tv_str
    ))

# and finally, the IRL standings
print()
print("Eastern Conference Standings:")
east = fstandings_f.loc[fstandings_f['CONFERENCE'] == 'East']
east = east[['TEAM', 'W', 'L']]
east['TEAM'] = east['TEAM'].str.pad(13)
print(east[:8].to_string(index=False))
print('*'*25)
print(east[8:].to_string(index=False, header=False))

print()
print("Western Conference Standings:")
west = fstandings_f.loc[fstandings_f['CONFERENCE'] == 'West']
west = west[['TEAM', 'W', 'L']]
west['TEAM'] = west['TEAM'].str.pad(13)
print(west[:8].to_string(index=False))
print('*'*25)
print(west[8:].to_string(index=False, header=False))
