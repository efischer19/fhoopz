import csv
from datetime import date, timedelta
from os import path
import pandas as pd

from nba_api.stats.endpoints import leaguegamefinder, scoreboardv2

basepath = path.dirname(path.dirname(path.abspath(__file__)))
data_path = path.join(basepath, 'data', 'irl')

def write_data_file_for_date(date_param):
    date_api_str = date_param.strftime("%m/%d/%Y")  # the only format the NBA API accepts for some reason
    print("getting data for {}".format(date_api_str))

    gf = leaguegamefinder.LeagueGameFinder(
        date_from_nullable=date_api_str,
        date_to_nullable=date_api_str,
        player_or_team_abbreviation='P',  # per-player stats instead of per-team
        league_id_nullable='00'  # NBA only
    )
    frame = gf.get_data_frames()[0]
    # since my csv files are partitioned by date, season_id and game_date can be dropped
    # also, 'MATCHUP' contains the team abbrev, and team names change infrequently enough that it's not worth storing for every game log
    # I keep everything else passed back by the API though
    frame.drop(['SEASON_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'GAME_DATE'], axis=1, inplace=True)
    frame.to_csv(path.join(data_path, 'game_logs', date_param.strftime('%Y-%m-%d.csv')), index=False)

today = date.today()
first_day = date(2019, 10, 21)  # hardcoded, I know this was the (day before the) first day of the season
date_in_question = first_day

while path.exists(path.join(data_path, 'game_logs', date_in_question.strftime('%Y-%m-%d.csv'))):
    date_in_question = date_in_question + timedelta(1)

# I now have the first date that does not exist; I want to go back and update the last one that *does* in case it's incomplete
if date_in_question is not first_day:  # unless we're rebuilding the whole season, naturally
    date_in_question = date_in_question - timedelta(1)

while date_in_question <= today:
    write_data_file_for_date(date_in_question)
    date_in_question = date_in_question + timedelta(1)

# now, let's fetch up-to-date standings and schedule (for today) data
print("getting today's schedule and league standings")
s = scoreboardv2.ScoreboardV2(day_offset=0, game_date=today.strftime("%m/%d/%Y"), league_id="00")
df = s.get_data_frames()
games_f = df[0][['GAME_ID', 'GAME_STATUS_TEXT', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID', 'NATL_TV_BROADCASTER_ABBREVIATION']]
games_f.columns = ['GAME_ID', 'START_TIME', 'HOME_ID', 'AWAY_ID', 'NATL_TV']
games_f.to_csv(path.join(data_path, 'schedule', today.strftime('%Y-%m-%d.csv')), index=False)

teams_f = pd.concat([df[4], df[5]])
teams_f = teams_f[['TEAM_ID', 'CONFERENCE', 'TEAM', 'G', 'W', 'L', 'W_PCT']]
teams_f.sort_values(by=['CONFERENCE', 'W_PCT'])
teams_f.to_csv(path.join(data_path, 'standings', today.strftime('%Y-%m-%d.csv')), index=False)
