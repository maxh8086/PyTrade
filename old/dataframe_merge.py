import pandas as pd


df1 = pd.DataFrame({'rkey': ['foo', 'bar', 'baz', 'fo'],
                    'value': [1, 2, 3, 5]})
df2 = pd.DataFrame({'rkey': ['foo', 'bar', 'baz', 'fo'],
                    'value': [6, 7, 8, 9]})
print(df1)

print(df2)
merged_df = df1.merge(df2, how = 'inner', on = 'rkey', suffixes=("_df1", "_df2"))
print(merged_df)