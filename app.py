import altair as alt
import polars as pl
import streamlit as st

from db import db_funcs
import src.main as main
from data.texts import GermanTextStorage, EnglishTextStorage, TextStorage

@st.cache_data
def run_strategy(strategy_dict:dict)->dict:
    result_dict = main.run(strategy_dict)
    return result_dict

def select_lang_and_index()->tuple[bool, str]:
    indices_available = ['MSCI World','DAX','S&P500','NASDAQ']
    left, _, right = st.columns(3, vertical_alignment="bottom")
    german_language = left.toggle(
        ':de:',
        key='german_language')
    index_chosen = right.selectbox(
        text_store.index_choice_label,
        indices_available,
    )
    return (german_language, index_chosen)

def get_lang_specific_texts()->TextStorage:
    if 'german_language' not in st.session_state:
        st.session_state['german_language'] = False
    if st.session_state['german_language']:
        text_store = GermanTextStorage()
    else:
        text_store = EnglishTextStorage()
    
    return text_store

def add_year_slider()->None:
    min_year = quote_data['Date'].min().year
    max_year = quote_data['Date'].max().year
    st.slider(text_store.slider_label, min_year, max_year,(min_year, max_year), key='date_tuple')
    return

def plot_index_line_chart()->None:
    c = alt.Chart(quote_data).mark_line().encode(
        alt.X('Date').title(text_store.chart_x_axis),
        alt.Y('Close').scale(zero=False).title(text_store.chart_y_axis)
        )
    st.altair_chart(c, use_container_width=True)
    return

def select_strategy_and_time_horizon()->tuple[str,int]:
    # Set up row elements with two columns
    left, right = st.columns(2, vertical_alignment="top")
    
    # Chose strategy
    strategy_chosen = left.radio(text_store.strategy_choice_label,
                            [text_store.strategy_1_name, text_store.strategy_2_name],
                            captions=[
            text_store.strategy_1_description,
            text_store.strategy_2_description,])

    # Prepare mapping of investment horizon strings to ints
    horizon_options = [5, 10, 15, 20]
    investment_horizon_mapping = {f'{year} {text_store.years}':year 
                                  for year in horizon_options}
    investment_horizon_mapping['max'] = 0

    default_year_index = list(investment_horizon_mapping.values()).index(10)
    investment_horizon_choice = right.selectbox(
        text_store.investment_horizon,
        list(investment_horizon_mapping.keys()),
        index=default_year_index)
    investment_horizon = investment_horizon_mapping[investment_horizon_choice]
    
    return (strategy_chosen, investment_horizon)

def select_strategy_inputs()->tuple[str, int, int]:
    match strategy_chosen:
        case text_store.strategy_1_name:
            strategy = 'down_percent_pure'
            down_percent = st.number_input(text_store.down_percent_description, 0, 100, 0)
            max_months = 0
        
        case text_store.strategy_2_name:
            strategy = 'down_percent_max_n_months'
            down_percent = st.number_input(text_store.down_percent_description, 0, 100, 0)
            max_months = st.number_input(text_store.max_months_description, 1, 600, 12)
    return (strategy, down_percent, max_months)

def display_results()->None:
    st.write((text_store.average_return_text + str(result_dict["average_annualized_return"]) + '%'
            + text_store.confidence_interval_part_1 + str(result_dict["bottom_pctile"]) + '% ' 
            + text_store.confidence_interval_part_2 + str(result_dict["top_pctile"]) + '%]'))
    st.write(text_store.average_days_text + str(result_dict["average_days_waited"]))
    st.write(text_store.not_invested_share_text + str(result_dict["perc_not_invested"]) + '%')
    return

# Read in texts according to language set
text_store = get_lang_specific_texts()

# Set title of page
st.title(text_store.title)

# USER INTERACTION: Select Index & language to use
german_language, index_chosen = select_lang_and_index()

# Load data from CSVs
quote_data = main.import_historical_quote_data(index_chosen)

# Normalize index levels to start at 100
quote_data = main.normalize_prices(quote_data)

# USER INTERACTION: Add possibility to slice the date range
add_year_slider()

# Filter dataset according to date range chosen in slider
quote_data = quote_data.filter((pl.col('Date').dt.year() >= st.session_state['date_tuple'][0])
                               & (pl.col('Date').dt.year() <= st.session_state['date_tuple'][1]))

# Plot index prices as line chart
plot_index_line_chart()

# Add instructions
st.info(text_store.instructions)

# USER INTERACTION: Choose strategy
strategy_chosen, investment_horizon = select_strategy_and_time_horizon()

# Get strategy inputs from user
strategy, down_percent, max_months = select_strategy_inputs()

# Compile inputs in dict
strategy_dict = {
    'index':index_chosen,
    'min_year':st.session_state['date_tuple'][0],
    'max_year':st.session_state['date_tuple'][1],
    'strategy':strategy,
    'months':max_months,
    'percent':down_percent,
    'investment_horizon':investment_horizon
    }

# USER INTERACTION: Upon clicking button, run strategy
run_strategy_button = st.button(text_store.run_button_text)
if run_strategy_button:
    result_dict = run_strategy(strategy_dict)

    # Display results: 
    # TODO: Highlight results
    display_results()
    
    # TODO: Add option to use Cost-Average investing in x parts every x months
    
    # Display all past results in table
    
    # Clear table