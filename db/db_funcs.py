import pandas as pd
import polars as pl
import sqlalchemy
import streamlit as st

def create_sqlalchemy_engine()->sqlalchemy.Engine:
    from sqlalchemy import create_engine
    
    db_password = st.secrets['DB_PASSWORD']
    db_adress = st.secrets['DB_ADRESS']
    db_uri = f'postgresql://{db_adress}:{db_password}@aws-0-eu-central-1.pooler.supabase.com:6543/postgres'
    engine = create_engine(db_uri)
    
    return engine

def execute_sql_select_query(query:str)->list[dict]:
    from sqlalchemy import text
    
    # Create DB engine 
    engine = create_sqlalchemy_engine()
    
    # Establish connection to DB and execute SQL query
    with engine.connect() as connection:
        results = connection.execute(
            text(query)).fetchall()
        
    return results

def get_price_data_by_index(index:str)->pl.DataFrame:            
    query = f"""SELECT 
            date,
            closing_price
            FROM 
            prices
            JOIN indices
            ON prices.id_index = indices.id
            WHERE index = '{index}'
            ORDER BY date
            """
    results = execute_sql_select_query(query)
    result_df = pl.from_pandas(pd.DataFrame(results)).rename({'date':'Date', 'closing_price':'Close'})
    
    return result_df