import polars as pl

from config import THOUSAND_SEP, DATE_FORMAT
from src.trading_strategy import TradingStrategy


def import_historical_quote_data(path='daily_msci_world_2012.csv')->pl.DataFrame:
    
    # Read in df
    required_cols = ['Date', 'Close']
    optional_price_cols = ['Open', 'High', 'Low']
    all_cols = required_cols + optional_price_cols
    quotes_df = pl.read_csv(path, infer_schema_length=0)
    
    # For optional price cols ('Open', 'High', 'Low'), check if available, else copy from 'Close'
    quotes_df = quotes_df.with_columns([
        pl.col('Close').alias(col) for col in optional_price_cols if col not in quotes_df.columns
        ])
    quotes_df = quotes_df.select(all_cols)
    
    # Cast columns to their correct data types
    quotes_df = quotes_df.with_columns(pl.col('Date').str.to_date(format=DATE_FORMAT))
    quotes_df = quotes_df.with_columns([
        pl.col(price_col).str.replace(THOUSAND_SEP, '').cast(pl.Float64) for price_col in ['Close']+optional_price_cols
    ])
    
    # Normalize prices (set first value to 100)
    normalization_factor = 100 / quotes_df.filter(pl.col('Date') == pl.col('Date').min())['Close'][0]
    quotes_df = quotes_df.with_columns(
        [pl.col(col).mul(normalization_factor) for col in ['Close']+optional_price_cols]    
    )
    
    return quotes_df

def calculate_total_return_from_df(quotes_df:pl.DataFrame, date_df:pl.DataFrame, price_type='Close')->pl.DataFrame:
    # Add prices to start and investment dates
    date_df = (date_df.join(quotes_df.select(['Date', price_type]), left_on=['investment_date'], right_on=['Date'], how='inner')
               .rename({price_type:'investment_date_price'}))
    date_df = (date_df.join(quotes_df.select(['Date', price_type]), left_on=['end_date'], right_on=['Date'], how='inner')
               .rename({price_type:'end_date_price'}))
    
    # Calculate total return
    date_df = date_df.with_columns([
        ((pl.col('end_date_price') / pl.col('investment_date_price')-1)*100).round(2).alias('total_return'),
    ])
    
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

def run_strategy_for_multiple_start_dates(quotes_df:pl.DataFrame, start_dates:list, end_date:str, strategy_dict:str):
    
    # Instantiate trading strategy objects for all start dates
    all_trading_strategies = [TradingStrategy(quotes_df, start_date=x, end_date=end_date) for x in start_dates]
    
    # Choose strategy method accroding to input 
    strategy = strategy_dict['strategy']
    match strategy:
        case 'down_percent_pure':
            percent = strategy_dict['percent']
            investment_dates = [strategy.down_percent_pure(percent=percent) 
                                for strategy in all_trading_strategies]
        case 'down_percent_max_n_months':
            percent = strategy_dict['percent']
            months = strategy_dict['months']
            investment_dates = [strategy.down_percent_max_n_months(percent=percent, months=months) 
                                for strategy in all_trading_strategies]
        case _:
            raise ValueError(f'Strategy {strategy} not defined!')
        
    return investment_dates

def get_strategy_results(quotes_df:pl.DataFrame, strategy_dict:dict)->pl.DataFrame:
    
    # Determine start and end dates
    end_date = quotes_df['Date'].max().strftime(DATE_FORMAT)
    all_start_dates = [x.strftime(DATE_FORMAT) for x in quotes_df['Date'].unique().to_list()]
    
    # Run strategy for all start days
    investment_dates = run_strategy_for_multiple_start_dates(quotes_df, all_start_dates, end_date, strategy_dict)
    
    # Create df from results
    strategy_result_df = (pl.from_dict(
        {'start_date':all_start_dates,
          'end_date':[end_date]*len(all_start_dates),
          'investment_date':investment_dates,
          })
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

def run(strategy_dict:dict, quotes_df:pl.DataFrame)->dict:
    
    # Run strategy to determine investment dates
    strategy_dates_df = get_strategy_results(quotes_df, strategy_dict)
    
    # Calculate returns
    strategy_result_df = calculate_total_return_from_df(quotes_df, strategy_dates_df, price_type='Close')
    
    # Calculate average annualized returns
    average_annualized_return_strategy = round(strategy_result_df['annualized_return'].mean(),2)
        
    # Calculate average waiting time
    average_days_waited = int(round(strategy_result_df['days_waited_to_invest'].mean(),0))
    
    # Calculate % of cases that did not invest at all over the time
    perc_not_invested = calculate_non_invested_percentage(strategy_result_df)
    
    # Compile results in dict
    result_dict = {
        'average_annualized_return':average_annualized_return_strategy,
        'average_days_waited':average_days_waited,
        'perc_not_invested':perc_not_invested,
    }
    
    return result_dict