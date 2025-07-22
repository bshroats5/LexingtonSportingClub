# libraries
import pandas as pd

# fbref table link
url_df = 'https://fbref.com/en/squads/7622315f/Lexington-SC-Stats'
df = pd.read_html(url_df)
print(df)

# creating a data with the same headers but without multi indexing
df.columns = [' '.join(col).strip() for col in df.columns]

df = df.reset_index(drop=True)
df.head()
print(df)