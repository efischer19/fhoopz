from os import path
import pandas as pd

basepath = path.dirname(path.dirname(path.abspath(__file__)))
data_path = path.join(basepath, 'data', 'fantasy', 'stats', 'fteams.csv')

df = pd.read_csv(data_path, usecols=range(1,12))
print(df.to_string(index=False))
