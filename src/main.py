import bisect
import datetime
import polars as pl

from config import THOUSAND_SEP, DATE_FORMAT, DATE_SEP, MONTH_DAYS
from db import db_funcs
from src.trading_strategy import TradingStrategy
from src import utils


def import_historical_quote_data(index='MSCI World')->pl.DataFrame:
    
    # Map index to file
    index_file_mapping = {
    'MSCI World':'data/daily_msci_world.csv',
    'DAX':'data/daily_DAX.csv',
    'S&P500':'data/daily_S&P500.csv',
    'NASDAQ':'data/daily_NASDAQ.csv',
    }
    path = index_file_mapping[index]
    
    # Read in df
    required_cols = ['Date', 'Close']
    quotes_df = pl.read_csv(path, infer_schema_length=0)
    quotes_df = quotes_df.select(required_cols)
    
    # Clean df by casting datatypes and normalizing prices
    quotes_df = cast_datatypes(quotes_df)
    quotes_df = normalize_prices(quotes_df)
    
    return quotes_df
    
def cast_datatypes(df:pl.DataFrame):
    # Cast columns to their correct data types
    df = df.with_columns(pl.col('Date').str.to_date(format=DATE_FORMAT))
    df = df.with_columns([
        pl.col(price_col).str.replace(THOUSAND_SEP, '').cast(pl.Float64) for price_col in ['Close']
    ])
    return df

def normalize_prices(df:pl.DataFrame):
    # Normalize prices (set first value to 100)
    normalization_factor = 100 / df.filter(pl.col('Date') == pl.col('Date').min())['Close'][0]
    df = df.with_columns(
        [pl.col(col).mul(normalization_factor) for col in ['Close']]    
    )
    return df

def add_cost_average_strategy_dates(df:pl.DataFrame, all_dates:list, over_n_months:int):
    """Add n "new_investment_dates" to the df, one new date every month"""

    # Prepare input data
    all_dates = sorted(all_dates)
    df = df.sort(by='investment_date')
    start_dates = df['start_date'].to_list()
    investment_dates =  df['investment_date'].to_list()
    end_dates = df['end_date'].to_list()
    
    investment_date_new_investment_date_dicts = []
    for i, investment_date in enumerate(investment_dates):
        investment_date_dict = {}
        new_investment_dates = []
        for n in range(0, over_n_months+1):
            new_investment_date = investment_date + datetime.timedelta(days=n*MONTH_DAYS)
            new_investment_date_index = bisect.bisect_left(all_dates, new_investment_date)
            if new_investment_date_index < len(all_dates):
                if new_investment_date <= end_dates[i]:
                    new_investment_dates.append(all_dates[new_investment_date_index])
        investment_date_dict['start_date'] = start_dates[i]
        investment_date_dict['new_investment_date'] = new_investment_dates
        investment_date_new_investment_date_dicts.append(investment_date_dict)
    
    full_df = pl.from_dicts(investment_date_new_investment_date_dicts).explode('new_investment_date')
    
    return full_df

def calculate_total_return_from_df(quotes_df:pl.DataFrame, date_df:pl.DataFrame, strategy_dict:dict)->pl.DataFrame:
    
    # Add prices to start and investment dates
    date_df = (date_df.join(quotes_df.select(['Date', 'Close']), left_on=['investment_date'], right_on=['Date'], how='inner')
               .rename({'Close':'investment_date_price'}))
    date_df = (date_df.join(quotes_df.select(['Date', 'Close']), left_on=['end_date'], right_on=['Date'], how='inner')
               .rename({'Close':'end_date_price'}))
    
    # Optionally add investment dates from Cost Average Strategy
    over_n_months = strategy_dict['cost_average_months']
    if over_n_months:
        cost_average_date_df = add_cost_average_strategy_dates(date_df, quotes_df['Date'].to_list(), over_n_months)
        cost_average_date_df = cost_average_date_df.join(quotes_df.rename({'Date':'new_investment_date', 
                                                                          'Close':'new_investment_date_price'})
                                                         .select(['new_investment_date', 'new_investment_date_price']),
                                                         on='new_investment_date')
        date_df = date_df.join(cost_average_date_df, how='left', on='start_date')
    else:
        date_df = date_df.with_columns([pl.col('investment_date').alias('new_investment_date'),
                                        pl.col('investment_date_price').alias('new_investment_date_price')])
        
    # Calculate total return
    date_df = date_df.with_columns([
        ((pl.col('end_date_price') / pl.col('new_investment_date_price')-1)*100).round(2).alias('total_return'),
    ])
    
    # Combine returns from same start date (cost average strategy) and calculate (equally weighted) return
    average_returns_by_start_date = date_df.group_by('start_date').agg(pl.mean('total_return')).sort(by='start_date')
    date_df = (date_df
               .drop(['new_investment_date','new_investment_date_price', 'total_return']).unique()
               .join(average_returns_by_start_date, on='start_date')
               .sort(by='start_date'))
    
    
    # Calculate time waited to deploy strategy
    date_df = date_df.with_columns([
        (pl.col('investment_date') - pl.col('start_date')).dt.total_days().alias('days_waited_to_invest'),
        (pl.col('end_date') - pl.col('investment_date')).dt.total_days().alias('days_invested'),
    ])
    
    # Calculate annualized returns
    date_df = date_df.with_columns([
        (((1 + pl.col('total_return')/100).pow((365/pl.col('days_invested'))) - 1)*100).round(2).alias('annualized_return'),
    ])
    
    return date_df

def run_strategy_for_multiple_start_dates(quotes_df:pl.DataFrame, start_dates:list, end_dates:list, strategy_dict:str)->list[dict]:
    
    # Instantiate trading strategy objects for all start and end dates
    all_trading_strategies = [TradingStrategy(quotes_df, start_date=start_date, end_date=end_date) 
                              for start_date, end_date in zip(start_dates, end_dates)]
    
    # Drop strategies without an end date (as none was found in the df that fit the criteria)
    all_trading_strategies = [strat for strat in all_trading_strategies if strat.end_date]
    
    # Choose strategy method accroding to input 
    match strategy_dict['strategy']:
        case 'down_percent_pure':
            strategy_dates = [{
                'start_date':strategy.start_date,
                'investment_date':strategy.down_percent_pure(percent=strategy_dict['percent']),
                'end_date':strategy.end_date} 
                                for strategy in all_trading_strategies]
        case 'down_percent_max_n_months':
            strategy_dates = [{
                'start_date':strategy.start_date,
                'investment_date':strategy.down_percent_max_n_months(percent=strategy_dict['percent'], 
                                                                     months=strategy_dict['months']),
                'end_date':strategy.end_date} 
                                for strategy in all_trading_strategies]
        case _:
            raise ValueError(f'Strategy {strategy_dict["strategy"]} not defined!')
        
    return strategy_dates

def get_strategy_results(quotes_df:pl.DataFrame, strategy_dict:dict)->pl.DataFrame:
    
    # Determine start and end dates
    max_end_date = quotes_df['Date'].max().strftime(DATE_FORMAT)
    all_start_dates = [x.strftime(DATE_FORMAT) for x in quotes_df['Date'].unique().to_list()]
    
    # If an investment horizon is specified, set end dates to start date + investment horizon
    if strategy_dict['investment_horizon'] != 0:
        end_dates = [utils.add_n_years_to_date(start_date, strategy_dict['investment_horizon']) for start_date in all_start_dates]
        
        # Check that at least one end date is in the selected timeframe, catch cases where investment horizon > selected timeframe
        end_dates_in_df = [utils.find_next_date_in_df(quotes_df, date=date) for date in end_dates]
        if not any(end_dates_in_df):
            raise ValueError(f'Investment horizon larger than selected period, please adjust!')
        
    else:
        end_dates = [max_end_date]*len(all_start_dates)
    
    # Run strategy for all start days
    strategy_date_dicts = run_strategy_for_multiple_start_dates(quotes_df, all_start_dates, end_dates, strategy_dict)
    
    # Create df from results
    strategy_result_df = (pl.from_dicts(strategy_date_dicts)
        .with_columns([
            pl.col('start_date').str.strptime(pl.Date, DATE_FORMAT),
            pl.col('investment_date').str.strptime(pl.Date, DATE_FORMAT),
            pl.col('end_date').str.strptime(pl.Date, DATE_FORMAT),
            ])
        )
    
    return strategy_result_df

def calculate_non_invested_percentage(strategy_result_df:pl.DataFrame)->float:
    
    strategy_result_df = strategy_result_df.with_columns([
        (pl.col('end_date') == pl.col('investment_date')).alias('not_invested')
    ])
    
    # Accound for last day (would always be counted as "not invested")
    number_dates_not_invested = strategy_result_df['not_invested'].sum() - 1
    total_number_dates = strategy_result_df['not_invested'].count() -1
    
    # Prevent 0 division cases (if always invested)
    if number_dates_not_invested <= 0:
        return 0.0
    
    non_invested_perc = round((number_dates_not_invested/total_number_dates)*100,2)
    
    return non_invested_perc

def run(strategy_dict:dict)->dict:
    
    # Read in data
    quotes_df = import_historical_quote_data(strategy_dict['index'])
    quotes_df = quotes_df.filter((pl.col('Date').dt.year() >= strategy_dict['min_year'])
                               & (pl.col('Date').dt.year() <= strategy_dict['max_year']))
    
    # Run strategy to determine investment dates
    strategy_dates_df = get_strategy_results(quotes_df, strategy_dict)
    
    # Calculate returns
    strategy_result_df = calculate_total_return_from_df(quotes_df, strategy_dates_df, strategy_dict)
    
    # Calculate average annualized returns
    average_annualized_return_strategy = round(strategy_result_df['annualized_return'].mean(),2)
    
    # Calculate 95%-CI of returns
    bottom_pctile = round(strategy_result_df['annualized_return'].quantile(0.025),2)
    top_pctile = round(strategy_result_df['annualized_return'].quantile(0.975),2)
        
    # Calculate average waiting time
    average_days_waited = int(round(strategy_result_df['days_waited_to_invest'].mean(),0))
    
    # Calculate % of cases that did not invest at all over the time
    perc_not_invested = calculate_non_invested_percentage(strategy_result_df)
    
    # Compile results in dict
    result_dict = {
        'average_annualized_return':average_annualized_return_strategy,
        'average_days_waited':average_days_waited,
        'perc_not_invested':perc_not_invested,
        'bottom_pctile':bottom_pctile,
        'top_pctile':top_pctile,
    }
    
    return result_dict
