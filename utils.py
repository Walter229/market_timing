import polars as pl

from config import DATE_SEP

def find_next_date_in_df(df:pl.DataFrame, date:str)->str:
    date_tuple = (int(x) for x in date.split(DATE_SEP))
    relevant_dates = df.filter(pl.col('Date') >= pl.date(*date_tuple))
    next_date_df = relevant_dates.select(pl.col('Date').min())
    
    # Check if data from the same or a later date available, else return empty string
    if not next_date_df.is_empty():
        next_date = next_date_df['Date'].dt.strftime('%Y-%m-%d')[0]
    else:
        next_date = ''
        
    return next_date

def get_polars_date_from_str(date_str:str)->pl.Date:
    return pl.date(*(int(x) for x in date_str.split(DATE_SEP)))

def get_price_of_day(df:pl.DataFrame, date_str:str, price_type='Close')->float:
    return df.filter(pl.col('Date')==get_polars_date_from_str(date_str))[price_type][0]