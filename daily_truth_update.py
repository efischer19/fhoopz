# standard imports
import boto3
from datetime import date, timedelta
from io import StringIO

# from layers
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, scoreboardv2

# constants
bucket_path = "www.eric-fischer.codes"
data_path_prefix = "fhoopz/data/irl"
s3_resource = boto3.resource("s3")
bucket = s3_resource.Bucket(bucket_path)
today = date.today()

def write_dataframe_to_csv_on_s3(dataframe, filename, bucket):
    """ Write a dataframe to a CSV on S3 """
    #https://towardsdatascience.com/introduction-to-amazon-lambda-layers-and-boto3-using-python3-39bd390add17

    csv_buffer = StringIO()
    dataframe.to_csv(csv_buffer, sep="\t", index=False)
    response = s3_resource.Object(bucket, filename).put(
        ACL='public-read',
        Body=csv_buffer.getvalue()
    )

def write_data_file_for_date(date_param):
    date_api_str = date_param.strftime("%m/%d/%Y")  # the only format the NBA API accepts for some reason

    gf = leaguegamefinder.LeagueGameFinder(
        date_from_nullable=date_api_str,
        date_to_nullable=date_api_str,
        player_or_team_abbreviation='P',  # per-player stats instead of per-team
        league_id_nullable='00'  # NBA only
    )
    frame = gf.get_data_frames()[0]
    """
    since my csv files are partitioned by date, season_id and game_date can be dropped
    also, 'MATCHUP' contains the team abbrev, and team names change infrequently enough that it's not worth storing for every game log
    I keep everything else passed back by the API though
    """
    frame.drop(['SEASON_ID', 'TEAM_NAME', 'TEAM_ABBREVIATION', 'GAME_DATE'], axis=1, inplace=True)
    write_dataframe_to_csv_on_s3(frame, "{}/game_logs/{}".format(data_path_prefix, date_param.strftime('%Y-%m-%d.csv')), bucket_path)

def find_last_existing_day():
    first_day = date(2021, 10, 19)  # hardcoded, I know this was the first day of the season
    date_in_question = first_day

    existing_data = [obj.key for obj in list(bucket.objects.filter(Prefix=data_path_prefix))]
    while "{}/game_logs/{}".format(data_path_prefix, date_in_question.strftime('%Y-%m-%d.csv')) in existing_data:
        date_in_question = date_in_question + timedelta(1)

    # I now have the first date that does not exist; I want to go back and update the last one that *does* in case it's incomplete
    if date_in_question is not first_day:  # unless we're rebuilding the whole season, naturally
        date_in_question = date_in_question - timedelta(1)

    return date_in_question

def write_daily_schedule_and_standings():
    s = scoreboardv2.ScoreboardV2(day_offset=0, game_date=today.strftime("%m/%d/%Y"), league_id="00")
    df = s.get_data_frames()
    schedule_frame = next(frame for frame in df if "NATL_TV_BROADCASTER_ABBREVIATION" in frame.columns)
    games_f = schedule_frame[['GAME_ID', 'GAME_STATUS_TEXT', 'HOME_TEAM_ID', 'VISITOR_TEAM_ID', 'NATL_TV_BROADCASTER_ABBREVIATION']]
    games_f.columns = ['GAME_ID', 'START_TIME', 'HOME_ID', 'AWAY_ID', 'NATL_TV']
    write_dataframe_to_csv_on_s3(games_f, "{}/schedule/{}".format(data_path_prefix, today.strftime('%Y-%m-%d.csv')), bucket_path)

    teams_f = pd.concat([frame for frame in df if "STANDINGSDATE" in frame.columns])
    teams_f = teams_f[['TEAM_ID', 'CONFERENCE', 'TEAM', 'G', 'W', 'L', 'W_PCT']]
    teams_f.sort_values(by=['CONFERENCE', 'W_PCT'])
    write_dataframe_to_csv_on_s3(teams_f, "{}/standings/{}".format(data_path_prefix, today.strftime('%Y-%m-%d.csv')), bucket_path)

# main function
#def lambda_handler(event, context):
def main():
    print("finding latest data date")
    current_date = find_last_existing_day()
    while current_date <= today:
        print("getting logs for {}".format(current_date))
        write_data_file_for_date(current_date)
        current_date = current_date + timedelta(1)

    print("Getting today's schedule and standings")
    write_daily_schedule_and_standings()
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

main()
print("done")
