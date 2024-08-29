import polars as pl

from config import THOUSAND_SEP, DATE_FORMAT
from trading_strategy import TradingStrategy


def import_historical_quote_data()->pl.DataFrame:
    date_cols = ['Date']
    price_cols = ['Close', 'Open', 'High', 'Low']
    quotes_df = pl.read_csv('historical_data_msci_world.csv').rename({'Price':'Close'}).select(date_cols+price_cols)
    #quotes_df = pl.read_csv('/Users/clemens/Desktop/Test.csv', separator=';').rename({'Price':'Close'}).select(date_cols+price_cols).drop_nulls()
    
    # Cast columns to their correct data types
    for date_col in date_cols:
        quotes_df = quotes_df.with_columns(pl.col(date_col).str.to_date(format='%m/%d/%Y'))
    for price_col in price_cols:
        quotes_df = quotes_df.with_columns(
        pl.col(price_col).str.replace(THOUSAND_SEP, '').cast(pl.Float32)
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

def run(strategy_dict:dict, quotes_df:pl.DataFrame)->None:
    
    # Run strategy to determine investment dates
    strategy_dates_df = get_strategy_results(quotes_df, strategy_dict)
    
    # Calculate returns
    strategy_result_df = calculate_total_return_from_df(quotes_df, strategy_dates_df, price_type='Close')
    
    # Calculate average and median annualized returns
    average_annualized_return_strategy = round(strategy_result_df['annualized_return'].mean(),2)
        
    return average_annualized_return_strategy