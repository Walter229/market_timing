import altair as alt
import polars as pl
import streamlit as st

import src.main as main

def run_strategy(strategy_dict:dict, _quote_df:pl.DataFrame)->float:
    average_annualized_return = main.run(strategy_dict, _quote_df)
    return average_annualized_return

st.title('Time in the market vs timing the market!')

# Visualize data
path = 'monthly_msci_world_1979.csv'
quote_data = main.import_historical_quote_data(path)

# Add possibility to slice the date range
min_year = quote_data['Date'].min().year
max_year = quote_data['Date'].max().year
values = st.slider("Date range to consider",min_year, max_year,(min_year, max_year), key='date_tuple')

# Filter dataset according to date range chosen in slider
quote_data = quote_data.filter((pl.col('Date').dt.year() >= st.session_state['date_tuple'][0])
                               & (pl.col('Date').dt.year() <= st.session_state['date_tuple'][1]))

# Plot line chart
c = alt.Chart(quote_data).mark_line().encode(
    alt.X('Date'),
    alt.Y('Close').scale(zero=False).title('MSCI World Index Level (normalized)')
    )
st.altair_chart(c, use_container_width=True)

# Add instructions
st.info('''
        Below you can set up a simple investment strategy and test how well it would have performed in the past.\n 
        For now, you have the possibility to wait for the market to first fall for x-% before you invest.
        Optionally, you can also specify a maximum time you would want to hold back your investment, before you
        end up investing anyways (even if the market did not fall enough according to your input).
        ''')

# Choose strategy
strategy_chosen = st.radio('Choose investment strategy:',
                           ['Market down x-%', 'Market down x-% (inc. max waiting time)'],
                           captions=[
        'Wait until the market goes down x-%',
        "Wait until the market goes down x-% (if it hasn't gone down after n-months, invest anyway)",
    ],)

# Get strategy inputs from user
match strategy_chosen:
    case 'Market down x-%':
        strategy = 'down_percent_pure'
        down_percent = st.number_input('How much should the market fall compare to today before you invest (in %)?', 0, 50, 0)
        max_months = 0
    
    case 'Market down x-% (inc. max waiting time)':
        strategy = 'down_percent_max_n_months'
        down_percent = st.number_input('How much should the market fall compare to today before you invest (in %)?', 0, 50, 0)
        max_months = st.number_input('How many months do you want to wait at most before investing?', 1, 120, 12)

# Compile inputs in dict
strategy_dict = {
    'strategy':strategy,
    'months':max_months,
    'percent':down_percent,
    }

# Upon clicking button, run strategy
run_strategy_button = st.button('Run strategy')
if run_strategy_button:
    average_annualized_return = run_strategy(strategy_dict, quote_data)

    # Display results
    st.write(f'Average return of your strategy: {average_annualized_return}% (per year)')