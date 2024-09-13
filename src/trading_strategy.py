from datetime import datetime
from dateutil.relativedelta import relativedelta
import polars as pl

from src import utils
from config import DATE_FORMAT, MONTH_DAYS

class TradingStrategy():
    def __init__(self, df:pl.DataFrame, start_date:str, end_date:str) -> None:
        self.df = df
        self.start_date = utils.find_next_date_in_df(df, start_date)
        self.end_date = utils.find_next_date_in_df(df, end_date)
    
    def down_percent_pure(self, percent)->str:
        """Determine buy date by waiting until price drops by X-percent
        
        Args:
            percent (int): percentage drop to wait for
            
        Returns:
            str: Date of purchase - if no date found, returns end date, leading to 0 return
        """
        start_price = utils.get_price_of_day(self.df, self.start_date, price_type='Close')
        buy_threshold = start_price - (percent/100)*start_price
        buy_date_df = self.df.filter((pl.col('Close') <= buy_threshold)&(pl.col('Date')>=utils.get_polars_date_from_str(self.start_date)))
        buy_date_df = buy_date_df.filter(pl.col('Date') == pl.col('Date').min())
        
        if buy_date_df.is_empty():
            return self.end_date
        
        return buy_date_df['Date'].dt.strftime(DATE_FORMAT)[0]
    
    def down_percent_max_n_months(self, percent:int, months:int)->str:
        """Determine buy date by waiting until price drops by X-percent. Wait max n months, 
        buy afterwards if still not dropped below 

        Args:
            percent (int): percentage drop to wait for
            months (int): max months to wait

        Returns:
            str: Date of purchase
        """
        # Get earliest date when price drops x percent
        buy_date = self.down_percent_pure(percent)
        
        # Check if date is less that n months after start date
        start_buy_day_dif = (datetime.strptime(buy_date,DATE_FORMAT) 
                             - datetime.strptime(self.start_date,DATE_FORMAT)).days
        start_buy_month_dif = start_buy_day_dif / MONTH_DAYS
        
        # If buy date is more than n months after start date, set buy date to start date + n months
        if start_buy_month_dif > months:
            buy_date = (datetime.strptime(self.start_date,DATE_FORMAT) 
                             + relativedelta(months=+months)).strftime(DATE_FORMAT)
        
        return buy_date
    