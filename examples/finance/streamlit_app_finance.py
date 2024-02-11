import sys

import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

#get yahoo finance
@st.cache_data
def get_yf(tickers):
    dict_yf = st.session_state['dict_yf']
    keys = list(dict_yf.keys())
    
    for ticker in tickers:
        if ticker not in keys:
            dict_yf[ticker] = yf.Ticker(ticker)
    
    st.session_state['dict_yf'] = dict_yf

#get stock price
@st.cache_data  # 👈 Add the caching decorator
def get_stock_price(ticker, period, interval):

    df = yf.download(ticker, period=period, interval=interval)
    
    return df

st.title('📉 Stock Price Survey')

#input ticker
ticker = st.text_input('Enter ticker', 'AAPL')

# Initialization
if 'tickers' not in st.session_state:
    st.session_state['tickers'] = []
else:
    #重複削除
    st.session_state['tickers'] = list(set(st.session_state['tickers']))

if 'dict_yf' not in st.session_state:
    st.session_state['dict_yf'] = {}

if ticker not in st.session_state['tickers']:
    st.session_state['tickers'].append(ticker)
st.write(st.session_state['tickers'])

tickers = st.multiselect(
    'What are your favorite colors',
    st.session_state['tickers'],
    st.session_state['tickers'])

st.write('You selected:', tickers)

# get stock info
get_yf(tickers)
stock = yf.Ticker(ticker)

tab1, tab2, tab3, tab4, tab_requirement = st.tabs(["stock information", "stock prices", 
                                                   'dividends', 'financials', 
                                                   "requirements"])

#stock information
with tab1:
    #info
    for key, value in st.session_state['dict_yf'][ticker].info.items():
        if type(value) != str:
            st.write(key + ': ' + str(value))
        else:
            st.write(key + ': ' + str(value))

#stock prices
with tab2:
    periods = ('1d', '5d', '1mo', '3mo', '6mo', '1y', 
               '2y', '5y', '10y', 'ytd', 'max')
    period = st.selectbox(
        'Please select the period of time you wish to obtain',
        periods, index=3)
    st.write('You selected:', period)

    intervals = ('1m', '2m', '5m', '15m', '30m', '60m', 
                 '90m', '1h', '1d', '5d', '1wk', '1mo', 
                 '3mo')
    interval = st.selectbox(
        'Select the length of the candlestick',
        intervals, index=8)
    st.write('You selected:', interval)

    #moving average
    ma = st.slider('How old are you?', 5, 200, 25, 5)
    st.write("Moving average: ", ma)

    #get stock prices
    df_stockprices = get_stock_price(ticker, period, interval)

    #culc moving average
    df_stockprices['Adj Close_SMA'+str(ma)] = df_stockprices['Adj Close'].rolling(ma).mean()

    #culc Moving Average Deviation Rate
    df_stockprices['Deviation Rate'] = (df_stockprices['Adj Close'] - df_stockprices['Adj Close_SMA'+str(ma)]) / df_stockprices['Adj Close_SMA'+str(ma)]

    #show chart
    fig = px.line(df_stockprices, x=df_stockprices.index, y=['Adj Close', 'Adj Close_SMA'+str(ma)]
                  , title='Stock price' + ticker)
    st.plotly_chart(fig, use_container_width=True)

    fig = px.line(df_stockprices, x=df_stockprices.index, y='Deviation Rate'
                  , title='Moving Average Deviation Rate ' + ticker)
    st.plotly_chart(fig, use_container_width=True)

    #show dataframe
    st.dataframe(df_stockprices)

#dividends
with tab3:
    df_dividends = pd.DataFrame()
    #get dividends
    df_dividends['Dividends'] = st.session_state['dict_yf'][ticker].dividends

    term = st.radio(
    "Select the period for which you wish to total dividends.",
    ('All', 'Yearly'), horizontal=True)
    st.write('You selected ' + term)

    if term == 'All':
        #culc rate of change
        df_dividends['rate of change'] = df_dividends['Dividends'].pct_change()
        df_dividends_chart = df_dividends
    else:
        pass
        df_dividends_yearly = df_dividends.resample('YS').sum()
        df_dividends_yearly['rate of change'] = df_dividends_yearly['Dividends'].pct_change()
        df_dividends_chart = df_dividends_yearly
    
    #culc rate of change
    df_dividends['rate of change'] = df_dividends['Dividends'].pct_change()
    #show chart
    fig = px.bar(df_dividends_chart, x=df_dividends_chart.index, y='Dividends'
                  , title='Dividend ' + ticker)
    st.plotly_chart(fig, use_container_width=True)
    
    fig = px.line(df_dividends_chart, x=df_dividends_chart.index, y='rate of change'
                  , title='Dividend rate of change ' + ticker)
    st.plotly_chart(fig, use_container_width=True)
    
    #show dataframe
    st.dataframe(df_dividends_chart)

#financials
with tab4:
    pass
    df_income_stmt = st.session_state['dict_yf'][ticker].income_stmt
    st.dataframe(df_income_stmt)

with tab_requirement:
    #version
    st.write('python: ', sys.version)
    st.write('yfinance: ', yf.__version__)
    st.write('pandas: ', pd.__version__)
    st.write('streamlit: ', st.__version__)