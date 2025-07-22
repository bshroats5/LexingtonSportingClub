# libraries
import pandas as pd

# fbref table link
url_df = 'https://fbref.com/en/squads/7622315f/Lexington-SC-Stats'
df = pd.read_html(url_df)
print(df)