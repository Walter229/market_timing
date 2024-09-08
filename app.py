import altair as alt
import polars as pl
import streamlit as st

import src.main as main
from data.texts import GermanTextStorage, EnglishTextStorage

@st.cache_data
def run_strategy(strategy_dict:dict)->dict:
    quote_df = main.import_historical_quote_data(strategy_dict['file'])
    quote_df = quote_df.filter((pl.col('Date').dt.year() >= strategy_dict['min_year'])
                               & (pl.col('Date').dt.year() <= strategy_dict['max_year']))
    result_dict = main.run(strategy_dict, quote_df)
    return result_dict

# Read in texts according to language set
if 'german_language' not in st.session_state:
    st.session_state['german_language'] = False
if st.session_state['german_language']:
    text_store = GermanTextStorage()
else:
    text_store = EnglishTextStorage()

# Set title of page
st.title(text_store.title)

# USER INTERACTION: Select Index & language to use
index_file_mapping = {
    'MSCI World':'data/daily_msci_world.csv',
    'DAX 40':'data/daily_DAX.csv',
    'S&P500':'data/daily_S&P500.csv',
    'NASDAQ 100':'data/daily_NASDAQ.csv',
}
left, _, right = st.columns(3, vertical_alignment="bottom")
german_language = left.toggle(
    ':de:',
    key='german_language')
index_chosen = right.selectbox(
    text_store.index_choice_label,
    list(index_file_mapping.keys()),
)

# Visualize data
path = index_file_mapping[index_chosen]
quote_data = main.import_historical_quote_data(path)

# USER INTERACTION: Add possibility to slice the date range
min_year = quote_data['Date'].min().year
max_year = quote_data['Date'].max().year
values = st.slider(text_store.slider_label, min_year, max_year,(min_year, max_year), key='date_tuple')

# Filter dataset according to date range chosen in slider
quote_data = quote_data.filter((pl.col('Date').dt.year() >= st.session_state['date_tuple'][0])
                               & (pl.col('Date').dt.year() <= st.session_state['date_tuple'][1]))

# Plot line chart
c = alt.Chart(quote_data).mark_line().encode(
    alt.X('Date').title(text_store.chart_x_axis),
    alt.Y('Close').scale(zero=False).title(text_store.chart_y_axis)
    )
st.altair_chart(c, use_container_width=True)

# Add instructions
st.info(text_store.instructions)

# USER INTERACTION: Choose strategy
strategy_chosen = st.radio(text_store.strategy_choice_label,
                           [text_store.strategy_1_name, text_store.strategy_2_name],
                           captions=[
        text_store.strategy_1_description,
        text_store.strategy_1_description,])

# Get strategy inputs from user
match strategy_chosen:
    case text_store.strategy_1_name:
        strategy = 'down_percent_pure'
        down_percent = st.number_input(text_store.down_percent_description, 0, 100, 0)
        max_months = 0
    
    case text_store.strategy_2_name:
        strategy = 'down_percent_max_n_months'
        down_percent = st.number_input(text_store.down_percent_description, 0, 100, 0)
        max_months = st.number_input(text_store.max_months_description, 1, 600, 12)

# Compile inputs in dict
strategy_dict = {
    'file':path,
    'min_year':st.session_state['date_tuple'][0],
    'max_year':st.session_state['date_tuple'][1],
    'strategy':strategy,
    'months':max_months,
    'percent':down_percent,
    }

# USER INTERACTION: Upon clicking button, run strategy
run_strategy_button = st.button('Run strategy')
if run_strategy_button:
    result_dict = run_strategy(strategy_dict)

    # Display results: 
    # TODO: Highlight results
    st.write((text_store.average_return_text + str(result_dict["average_annualized_return"]) + '% '
            + text_store.confidence_interval_part_1 + str(result_dict["bottom_pctile"]) + '% ' 
            + text_store.confidence_interval_part_2 + str(result_dict["top_pctile"]) + '%]'))
    st.write(text_store.average_days_text + str(result_dict["average_days_waited"]))
    st.write(text_store.not_invested_share_text + str(result_dict["perc_not_invested"]) + '%')
    
    # TODO: Add option to set investment horizon (in years)
    
    # TODO: Add option to use Cost-Average investing in x parts every x months
    
    # Display all past results in table
    
    # Clear table