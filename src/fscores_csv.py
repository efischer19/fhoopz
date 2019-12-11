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

# first, let's build fplayers.csv
# player_id, player_name, ftotal, f_per_game, f_per_48
irl_totals = pd.read_csv(
    path.join(irl_data_path, "per_player", "totals.csv"),
    index_col='PLAYER_ID'
)
fvals = {}
with open(path.join(f_data_path, "settings", "scoring.json"), "r") as rfile:
    fvals = json.load(rfile)

def build_fdata(row, fvals):
    ftotal = sum([
        row[stat]*fvals[stat]
        for stat in fvals
    ])
    if row['MIN'] == 0:
        row['MIN'] = 1  # math is easier if we can assume all players have at least 1 minute
    return [
        row['PLAYER_NAME'],
        ftotal,
        float(round(Decimal(ftotal)/Decimal(row['G']), 3)),  # all players have >= 1 game, by virtue of having >= 1 log entry
        float(round(Decimal(ftotal)/Decimal(row['MIN'])*Decimal(48), 3))
    ]

fplayer_df = irl_totals.apply(build_fdata, axis=1, result_type='expand', fvals=fvals)
fplayer_df.columns = ['PLAYER_NAME', 'FPT_TOTAL', 'FPT_PER_G', 'FPT_PER_48']
fplayer_df.sort_values(by='FPT_TOTAL', ascending=False, inplace=True)
fplayer_df.to_csv(path.join(f_data_path, "stats", "players.csv"))

# now, we need to calculate fteam totals
# read in fteam rosters
# iterate over daily game logs, keep running totals
# calculate fpts, per-game, and per-48 averages at the end
# write it all out
roster_ref = {}
with open(path.join(f_data_path, "settings", "rosters.json"), "r") as rfile:
    roster_ref = json.load(rfile)

today = date.today()
first_day = date(2019, 10, 22)  # hardcoded, I know this was the first day of the season
date_in_question = first_day

# I make a lot of assumptions about rosters.json
# namely, the 'players' dict mapping days to roster arrays matters a lot
current_rosters = {}

fteam_stat_cats = list(fvals.keys()) + ['G', 'MIN']
fteam_totals = {
    team['id']: dict(zip(fteam_stat_cats, [0] * (len(fvals) + 2)))
    for team in roster_ref
}
for team in roster_ref:
    fteam_totals[team['id']]['TEAM_NAME'] = team['name']

def process_daily_logs(date_str, rosters, fteam_totals, fvals):
    df = pd.read_csv(path.join(irl_data_path, 'game_logs', date_str + ".csv"), index_col='PLAYER_ID')
    print('\n{:*^14}'.format(date_str))
    for tid, roster in rosters.items():
        for pid in roster:
            try:
                row = df.loc[pid]
                ftotal = sum([
                    row[stat]*fvals[stat]
                    for stat in fvals
                ])
                fstr = '{:21} ({:^11}): '.format(row['PLAYER_NAME'], row['MATCHUP'])
                for stat in fvals:
                    fstr += "{:2} {}, ".format(row[stat], stat)
                print(fstr + "{:6.2f} FPTS".format(ftotal))
                fteam_totals[tid]['G'] += 1
                fteam_totals[tid]['MIN'] += row['MIN'].item()  # errors arise if this stays as a numpy.int64
                for stat in fvals:
                    fteam_totals[tid][stat] += row[stat]
            except KeyError:
                continue  # every player does not play every day, this is fine

while date_in_question <= today:
    iso8601 = date_in_question.strftime("%Y-%m-%d")
    for team in roster_ref:
        if iso8601 in team['players']:
            current_rosters[team['id']] = team['players'][iso8601]
    process_daily_logs(iso8601, current_rosters, fteam_totals, fvals)
    date_in_question = date_in_question + timedelta(1)

with open(path.join(f_data_path, 'settings', 'latest_roster.csv'), 'w') as f:
    json.dump(current_rosters, f)

for tid in fteam_totals:
    ftotal = sum([fteam_totals[tid][stat]*fvals[stat] for stat in fvals])
    fteam_totals[tid]['FPT'] = ftotal
    fteam_totals[tid]['FPT_PER_G'] = float(round(Decimal(ftotal)/Decimal(fteam_totals[tid]['G']), 3))
    fteam_totals[tid]['FPT_PER_48'] = float(round(Decimal(ftotal)/Decimal(fteam_totals[tid]['MIN'])*Decimal(48), 3))

fteam_df = pd.DataFrame.from_dict(fteam_totals, orient='index')
fteam_df.sort_values(by='FPT', ascending=False, inplace=True)
fteam_cols = ['TEAM_NAME', 'FPT', 'FPT_PER_G', 'FPT_PER_48'] + [stat for stat in fvals] + ['G', 'MIN']
fteam_df = fteam_df.loc[:, fteam_cols]
fteam_df.to_csv(path.join(f_data_path, "stats", "fteams.csv"))
