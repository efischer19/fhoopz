from collections import defaultdict
import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import numpy as np
from os import path
import pandas as pd

from nba_api.stats.endpoints import leaguegamefinder

basepath = path.dirname(path.dirname(path.abspath(__file__)))
irl_data_path = path.join(basepath, 'data', 'irl')

# it'll actually be better to use a dict in-memory as I sum the totals, then write it to a csv as the very last step
def update_totals(date_param, totals):
    df = pd.read_csv(path.join(irl_data_path, 'game_logs', date_param.strftime('%Y-%m-%d.csv')), index_col='PLAYER_ID')
    for pid, data in df.iterrows():
        totals[pid]['PLAYER_NAME'] = data['PLAYER_NAME']
        for stat in counting_stats:
            if stat != 'G':
                totals[pid][stat] += data[stat]
        totals[pid]['G'] += 1

counting_stats = ['MIN', 'PTS', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS', 'G']
def default_stats():
    return dict(zip(counting_stats, [0] * 18))

# just sum up all the data, there's not that much of it and that makes handling problematic data in the past easier
# since I "build the world" every time this script runs, I can just remove problematic input data and re-run if needed

# pass 1: read all data, sum totals into in-memory dict as able
today = date.today()
first_day = date(2019, 10, 21)  # hardcoded, I know this was the (day before the) first day of the season
date_in_question = first_day
players_dict = defaultdict(default_stats)
while date_in_question <= today:
    print("Processing game logs from " + date_in_question.strftime("%Y-%m-%d"))
    update_totals(date_in_question, players_dict)
    date_in_question = date_in_question + timedelta(1)

# so now we have counting stats in a dictionary of the form { PLAYER_ID: [PLAYER_NAME, <counting stats>] }
# let's add percentages and averages, yeah? percentages can go into the existing dict; averages will be their own thing
for data in players_dict.values():
    try:
        data['FG_PCT'] = float(round(Decimal(data['FGM'])/Decimal(data['FGA']), 3))
    except InvalidOperation:
        data['FG_PCT'] = np.nan
    try:
        data['FG3_PCT'] = float(round(Decimal(data['FG3M'])/Decimal(data['FG3A']), 3))
    except InvalidOperation:
        data['FG3_PCT'] = np.nan
    try:
        data['FT_PCT'] = float(round(Decimal(data['FTM'])/Decimal(data['FTA']), 3))
    except InvalidOperation:
        data['FT_PCT'] = np.nan

# once that's done, throw it into a frame and write a csv
# PLAYER_ID not in this list; it's the index so it's special
ideal_column_order = ['PLAYER_NAME', 'MIN', 'PTS', 'FGM', 'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM', 'FTA', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PLUS_MINUS', 'G']
player_frame = pd.DataFrame.from_dict(players_dict, orient='index')
player_frame.sort_values(by='PTS', ascending=False, inplace=True)
player_frame.index.name = 'PLAYER_ID'
player_frame = player_frame.loc[:, ideal_column_order]
player_frame.to_csv(path.join(irl_data_path, "per_player", "totals.csv"))

# but that's not all! we can easily calculate per-game and per-48 averages, which are useful in a different way
per_game_dict = {}
per_48_dict = {}
for pid, data in players_dict.items():
    per_game_dict[pid] = { stat: float(round(Decimal(data[stat])/Decimal(data['G']), 3)) for stat in counting_stats }
    per_game_dict[pid]['PLAYER_NAME'] = data['PLAYER_NAME']
    del per_game_dict[pid]['G']  # all players should average 1 game per game, that's just a tautology and not worth saving

    if data['MIN'] > 0:
        per_48_dict[pid] = { stat: float(round(Decimal(data[stat])/Decimal(data['MIN'])*Decimal(48), 3)) for stat in counting_stats }
        per_48_dict[pid]['PLAYER_NAME'] = data['PLAYER_NAME']
        del per_48_dict[pid]['G']  # what would games-per-48 even mean? I'm sure it's related to playing time somehow... regardless, on we go
        del per_48_dict[pid]['MIN']  # everyone will likely average 48 minutes per 48 minutes

game_frame = pd.DataFrame.from_dict(per_game_dict, orient='index')
game_frame.sort_values(by='PTS', ascending=False, inplace=True)
game_frame.index.name = 'PLAYER_ID'
game_cols = game_frame.columns.to_list()
game_cols = game_cols[-1:] + game_cols[:-1]  # this just moves PLAYER_NAME to be next to the indexing PLAYER_ID; it reads more easily for humans
game_frame = game_frame.loc[:, game_cols]
game_frame.to_csv(path.join(irl_data_path, "per_player", "per_game.csv"))

min_frame = pd.DataFrame.from_dict(per_48_dict, orient='index')
min_frame.sort_values(by='PTS', ascending=False, inplace=True)
min_frame.index.name = 'PLAYER_ID'
min_cols = min_frame.columns.to_list()
min_cols = min_cols[-1:] + min_cols[:-1]  # this just moves PLAYER_NAME to be next to the indexing PLAYER_ID; it reads more easily for humans
min_frame = min_frame.loc[:, min_cols]
min_frame.to_csv(path.join(irl_data_path, "per_player", "per_48_minutes.csv"))
