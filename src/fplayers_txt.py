from os import path
import pandas as pd

basepath = path.dirname(path.dirname(path.abspath(__file__)))
data_path = path.join(basepath, 'data', 'fantasy', 'stats', 'players.csv')

df = pd.read_csv(data_path)
df = df[['PLAYER_NAME', 'PLAYER_ID', 'FPT_TOTAL', 'FPT_PER_G', 'FPT_PER_48']]
print(df.to_string(index=False))

