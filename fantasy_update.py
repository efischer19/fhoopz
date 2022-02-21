# also have a today's games blurb?

# future improvement: yesterday results, highlights

# future future improvement: betting lines for today

# initially copied from the code that builds eric-fischer.codes/nba.txt
# standard imports
import boto3
from datetime import datetime, date, timedelta
from io import StringIO
from os import path

# from layers
import pandas as pd

irl_team_info = [
    {"id": 1, "long": "Boston", "short": "BOS"},
    {"id": 2, "long": "New York", "short": "NYK"},
    {"id": 3, "long": "Brooklyn", "short": "BKN"},
    {"id": 4, "long": "Toronto", "short": "TOR"},
    {"id": 5, "long": "Philadelphia", "short": "PHI"},
    {"id": 6, "long": "Milwaukee", "short": "MIL"},
    {"id": 7, "long": "Indiana", "short": "IND"},
    {"id": 8, "long": "Chicago", "short": "CHI"},
    {"id": 9, "long": "Cleveland", "short": "CLE"},
    {"id": 10, "long": "Detroit", "short": "DET"},
    {"id": 11, "long": "Miami", "short": "MIA"},
    {"id": 12, "long": "Atlanta", "short": "ATL"},
    {"id": 13, "long": "Charlotte", "short": "CHA"},
    {"id": 14, "long": "Orlando", "short": "ORL"},
    {"id": 15, "long": "Washington", "short": "WAS"},
    {"id": 16, "long": "L.A. Lakers", "short": "LAL"},
    # the non-matching format of LA/L.A. is correct, in that it matches nbaapi data
    {"id": 17, "long": "LA Clippers", "short": "LAC"},
    {"id": 18, "long": "Sacramento", "short": "SAC"},
    {"id": 19, "long": "Golden State", "short": "GSW"},
    {"id": 20, "long": "Portland", "short": "POR"},
    {"id": 21, "long": "Dallas", "short": "DAL"},
    {"id": 22, "long": "San Antonio", "short": "SAS"},
    {"id": 23, "long": "Memphis", "short": "MEM"},
    {"id": 24, "long": "New Orleans", "short": "NOP"},
    {"id": 25, "long": "Phoenix", "short": "PHX"},
    {"id": 26, "long": "Utah", "short": "UTA"},
    {"id": 27, "long": "Denver", "short": "DEN"},
    {"id": 28, "long": "Oklahoma City", "short": "OKC"},
    {"id": 29, "long": "Houston", "short": "HOU"},
    {"id": 30, "long": "Minnesota", "short": "MIN"}
]

the_guys_fsquads = {
    "Kenny": [11, 1, 12, 28],
    "Steve": [6, 5, 20, 10],
    "Fish": [16, 2, 17, 9],
    "Zim": [8, 23, 7, 24],
    "Td": [3, 27, 4, 22],
    "Brett": [25, 21, 30, 13],
    "Zane": [19, 26, 18, 15]
}

# common setup
irl_data_path = 's3://www.eric-fischer.codes/fhoopz/data/irl/'
schedule_f = pd.read_csv(irl_data_path + 'schedule/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t')
standings_f = pd.read_csv(irl_data_path + 'standings/' + date.today().strftime('%Y-%m-%d.csv'), sep='\t', index_col='TEAM_ID')
today_txt = StringIO()
irl_team_fscores = {}

# the IRL standings
def _standings_helper(df, last_pts, last_w_pct, start_idx):
    ret = ""
    idx = start_idx
    for _, row in df.iterrows():
        team = row['TEAM'].rjust(13)
        pts = last_pts
        if row['W_PCT'] != last_w_pct:  # TODO: proper EOY tiebreakers for seeding?
            pts = 10-idx
            last_pts = pts
            last_w_pct = row['W_PCT']
        if pts > 0:
            for team_data in irl_team_info:
                if team_data['long'] in team:
                    irl_team_fscores[team_data['id']] = pts
            ret += "{} {}-{}, {} pts\n".format(team, row["W"], row["L"], pts)
        else:
            ret += "{} {}-{}\n".format(team, row["W"], row["L"])
        idx = idx + 1
    return ret, last_pts, last_w_pct

today_txt.write("*East:*\n```")
east = standings_f.loc[standings_f['CONFERENCE'] == 'East']
temp_str, last_pts, last_w_pct = _standings_helper(east[:6], 11, 1.1, 0)
today_txt.write(temp_str)
today_txt.write('-'*23)
today_txt.write("\n")
temp_str, last_pts, last_w_pct = _standings_helper(east[6:10], last_pts, last_w_pct, 6)
today_txt.write(temp_str)
today_txt.write('*'*23)
today_txt.write("\n")
temp_str, last_pts, last_w_pct = _standings_helper(east[10:], last_pts, last_w_pct, 10)
today_txt.write(temp_str)
today_txt.write("```\n\n")

today_txt.write("*West:*\n```")
west = standings_f.loc[standings_f['CONFERENCE'] == 'West']
temp_str, last_pts, last_w_pct = _standings_helper(west[:6], 11, 1.1, 0)
today_txt.write(temp_str)
today_txt.write('-'*23)
today_txt.write("\n")
temp_str, last_pts, last_w_pct = _standings_helper(west[6:10], last_pts, last_w_pct, 6)
today_txt.write(temp_str)
today_txt.write('*'*23)
today_txt.write("\n")
temp_str, last_pts, last_w_pct = _standings_helper(west[10:], last_pts, last_w_pct, 10)
today_txt.write(temp_str)
today_txt.write("```\n\n")

# fantasy leaderboard
today_txt.write("*Fantasy Leaderboard:*\n```")
flines = []
for name, team_list in the_guys_fsquads.items():
    teams_str = ""
    total = 0
    for idx, team in enumerate(team_list):
        irl_data = next(data for data in irl_team_info if data['id'] == team)
        teams_str += "{} {}".format(irl_data['short'], irl_team_fscores.get(irl_data['id'], 0))
        total += irl_team_fscores.get(irl_data['id'], 0)
        if idx < 3:
            teams_str += ", "
    flines.append("{}: {} [{}]".format(total, name, teams_str))

for line in sorted(flines, key=lambda l: (int)(l.split(':')[0]), reverse=True):
    today_txt.write(line)
    today_txt.write("\n")
today_txt.write("```\n\n")

#then, today's games (start time, away @ home (team names), national tv)
today_txt.write("_Today's games:_\n```")
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
today_txt.write("```")
print(today_txt.getvalue())
