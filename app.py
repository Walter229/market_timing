import streamlit as st

import main

@st.cache_data
def run_strategy(strategy_dict:dict)->tuple[float, float]:
    return main.run(strategy_dict)

st.title('Time in the market vs timing the market!')

# Visualize data
quote_data = main.import_historical_quote_data()
st.line_chart(quote_data, x="Date", y="Close", y_label='MSCI World Index')

# Add instructions
st.write('Choose your investment strategy to see how well it perfomed in the past!')

# Choose strategy
max_wait_toggle = st.toggle("Add maximum waiting time")

# Provide strategy inputs
max_months = 0
strategy = 'down_percent_pure'
down_percent = st.number_input('How much should the market fall compare to today before you invest (in %)?', 0, 50, 0)
if max_wait_toggle:
    strategy = 'down_percent_max_n_months'
    max_months = st.number_input('How many months do you want to wait at most before investing?', 0, 50, 0)
strategy_dict = {
    'strategy':strategy,
    'months':max_months,
    'percent':down_percent,
    }

# Upon clicking button, run strategy
run_strategy_button = st.button('Run strategy')
if run_strategy_button:
    average_annualized_return, median_annualized_return = run_strategy(strategy_dict)

    # Display results
    st.write(f'Average return of your strategy: {average_annualized_return}% (per year)')
    st.write(f'Median return of your strategy: {median_annualized_return}% (per year)')