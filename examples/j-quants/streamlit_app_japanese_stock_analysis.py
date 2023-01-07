import os
import json
from datetime import datetime
import io

import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import jquantsapi

#変数
#refresh_token
dict_refresh_token={}

#refresh_token の書き込み
def writing_refresh_token(refresh_token):
    pass

# 銘柄情報を取得します
@st.cache(suppress_st_warning=True)
def get_list():
    df_list = jqapi.get_list()
    return df_list

# code が4桁で入力されている場合は末尾に0を付与する
def add_zero(code):
    code_str=str(code)
    if len(code_str) == 4:
        code_str += "0"
    return code_str

#株価を取得
def get_prices_daily(code):
    df = jqapi.get_prices_daily_quotes(code=code)
    df=df.dropna(subset=['AdjustmentClose'])
    return df

#株価情報を取得
@st.cache(suppress_st_warning=True)
def get_price_range():
    # 株価情報を取得します (データ取得に約6分待ちます)
    now = pd.Timestamp.now(tz="Asia/Tokyo")
    # 過去6ヶ月のデータを取得
    start_dt = now - pd.Timedelta(190, unit="D")  # 計算用に10日分多めに指定しています
    end_dt = now
    if end_dt.hour < 19:
        # データ更新時間前の場合は日付を1日ずらします。
        end_dt -= pd.Timedelta(1, unit="D")
    #株価情報を取得
    df_p = jqapi.get_price_range(start_dt=start_dt, end_dt=end_dt)
    #df_p.reset_index(drop=True, inplace=True)

    return df_p

#財務情報を取得
@st.cache(suppress_st_warning=True)
def get_statements_range():
    # 過去3ヶ月に発表された財務情報を取得します
    now = pd.Timestamp.now(tz="Asia/Tokyo")
    start_dt = now - pd.Timedelta(90, unit="D")
    end_dt = now
    if end_dt.hour < 1:
        # データ更新時間前の場合は日付を1日ずらします。
        end_dt -= pd.Timedelta(1, unit="D")
    df_s = jqapi.get_statements_range(start_dt=start_dt, end_dt=end_dt)
    # float64にするために"-"をnp.nanに置き換えます
    df_s.replace({"－": np.nan}, inplace=True)
    df_s.replace('',np.nan, inplace=True)
    df_s["ResultDividendPerShareFiscalYearEnd"] = df_s["ResultDividendPerShareFiscalYearEnd"].astype(np.float64)
    df_s["EarningsPerShare"] = df_s["EarningsPerShare"].astype(np.float64)
    df_s["ForecastDividendPerShareAnnual"] = df_s["ForecastDividendPerShareAnnual"].astype(np.float64)
    df_s["ForecastEarningsPerShare"] = df_s["ForecastEarningsPerShare"].astype(np.float64)
    df_s.sort_values("DisclosedUnixTime", inplace=True)
    
    return df_s

#配当利回りを計算する
def culc_dividend(df_work,df_p_work):
    #df_work:財務情報
    #df_p_work:株価情報
    #return:df_work
    # 財務情報を銘柄ごとに重複を排除して最新の財務情報のみを使用します
    df_work.sort_values("DisclosedUnixTime", inplace=True)
    df_work = df_work.drop_duplicates(["LocalCode"], keep="last")
    # 終値が0の場合は前営業日の終値を使用します
    df_p_work.sort_values(["Code", "Date"], inplace=True)
    df_p_work["AdjustmentClose"].replace({0.0: np.nan}, inplace=True)
    df_p_work.loc[:, "AdjustmentClose"] = df_p_work.groupby("Code")["AdjustmentClose"].ffill()
    # 終値がnanの場合は翌営業日の終値を使用します (データの先頭)
    df_p_work.loc[:, "AdjustmentClose"] = df_p_work.groupby("Code")["AdjustmentClose"].bfill()
    # 各銘柄の直近のリターンを算出します
    def _calc_return(df, bdays):
        return (df["AdjustmentClose"].iat[-1] / df["AdjustmentClose"].iloc[-bdays:].iat[0]) - 1
    df_p_work.sort_values(["Code", "Date"], inplace=True)
    df_returns_1months = df_p_work.groupby("Code").apply(_calc_return, 20).rename("1ヶ月リターン")
    df_returns_3months = df_p_work.groupby("Code").apply(_calc_return, 60).rename("3ヶ月リターン")
    # リターンと結合します
    df_work = pd.merge(df_work, df_returns_1months, left_on=["LocalCode"], right_index=True, how="left")
    df_work = pd.merge(df_work, df_returns_3months, left_on=["LocalCode"], right_index=True, how="left")
    # 配当利回りを計算するために直近の終値を取得します
    df_close = df_p_work.loc[df_p_work["Date"] == df_p_work["Date"].max(), ["Code", "Date", "AdjustmentClose"]]
    # 直近の株価と結合します
    df_work = pd.merge(df_work, df_close, left_on=["LocalCode"], right_on=["Code"], how="left")
    # 配当利回りを算出します
    df_work["配当利回り"] = df_work["ResultDividendPerShareFiscalYearEnd"] / df_work["AdjustmentClose"]
    # 予想配当利回りを算出します
    df_work["予想配当利回り"] = df_work["ForecastDividendPerShareAnnual"] / df_work["AdjustmentClose"]

    # 配当性向を算出します
    df_work["配当性向"] = df_work["ResultDividendPerShareFiscalYearEnd"] / df_work["EarningsPerShare"] 
    # 予想配当性向を算出します
    df_work["予想配当性向"] = df_work["ForecastDividendPerShareAnnual"] / df_work["ForecastEarningsPerShare"]

    # 銘柄名と結合します
    df_work = pd.merge(df_work, df_list, left_on=["LocalCode"], right_on=["Code"])

    # 表示用に開示日を追加します
    df_work["開示日"] = df_work["DisclosedDate"].dt.strftime("%Y-%m-%d")

    # 表示する項目を指定します
    output_cols = [
        "LocalCode",
        "CompanyName",
        "開示日",
        "配当性向",
        "予想配当性向",
        "配当利回り",
        "予想配当利回り",
        "1ヶ月リターン",
        "3ヶ月リターン",
    ]
    df_work=df_work[output_cols]
    df_work=df_work.sort_values(["配当利回り"], ascending=False)

    return df_work
     

st.title("💹 Analyzing Japan's Stock Market")

with st.expander("See overview"):
    st.write('This is an application Japanese stock price analysis using jquants-api-client.')

#write refresh token
with st.expander("Write refresh tokens"):
    st.write("Get refresh tokens [link](https://application.jpx-jquants.com/)")
    st.write('Writing refresh tokens.')
    refresh_token = st.text_input("Enter refresh token", type="password")
    if len(refresh_token)>0:
        # 辞書の出力
        dict_refresh_token = {
            'refresh_token': refresh_token ,
        }
        st.download_button(
            label="Download data as JSON",
            data=json.dumps(dict_refresh_token),
            file_name='jquantsapi-key.json',
            mime='json',
        )
    st.write("reference url [link](https://github.com/J-Quants/jquants-api-client-python/blob/main/examples/20220825-000-write-refresh_token.ipynb)")

#read refresh token
with st.expander("Read refresh tokens"):
    st.write('Reading refresh tokens.')
    uploaded_file = st.file_uploader("Choose a json file")
    if uploaded_file is not None:
        # To convert to a string based IO:
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        # To read file as string:
        string_data = stringio.read()
        dict_refresh_token=json.loads(string_data)
        #st.json(dict_refresh_token)
        # J-Quants APIクライアントを初期化します
        jqapi = jquantsapi.Client(refresh_token=dict_refresh_token['refresh_token'])
    

#View Stock Information
with st.expander("View Stock Information"):
    if any(dict_refresh_token):
        df_list=get_list()
        st.dataframe(df_list)

#Get Stock
st.header('Price movement')
st.write('Plot the stock price trends.')
if any(dict_refresh_token):
    value_code=1301
    code = st.number_input('Insert a code',min_value=1000,max_value=9999,value=value_code,step=1)
    code_str=add_zero(code)
    if code_str in df_list['Code'].unique().tolist():
        st.write('The current code is ', code_str)
        df_list_work=df_list[df_list['Code']==code_str].copy()
        # Boolean to resize the dataframe, stored as a session state variable
        st.dataframe(df_list_work.T, use_container_width=True)
        df=get_prices_daily(code_str)
        #moving average
        SMA = st.slider('Moving average',min_value=5, max_value=200, value=50, step=5)
        df['SMA'+str(SMA)]=df["AdjustmentClose"].rolling(SMA).mean()
        #chart plotly
        fig = px.line(df, x="Date", y=["AdjustmentClose",'SMA'+str(SMA)], title=code_str+' price movement')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        st.dataframe(df)
    else:
        st.write('This code does not exist.')
st.write("reference url [link](https://github.com/J-Quants/jquants-api-client-python/blob/main/examples/20220825-001-price-movement.ipynb)")

#Secter
st.header('Sector')
st.write('Plot sector returns.')
if any(dict_refresh_token):
    tab1, tab2 ,tab3 = st.tabs(["Market segment", "Sector",'Returns by Sector'])
    with tab1:
        # 市場区分別の銘柄数を把握します。
        df_marketcode = df_list.groupby(["MarketCode", "MarketCodeName"]).count()
        #多い順にsort
        df_marketcode=df_marketcode.sort_values('Code', ascending=False)
        df_marketcode=df_marketcode.reset_index()
        df_marketcode['Count']=df_marketcode['Code']
        #chart plotly
        fig = px.bar(df_marketcode, x="MarketCodeName", y="Count", title='Number of stocks by market segment')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with tab2:
        # セクター別の銘柄数を把握します。
        df_marketcode = df_list.groupby(["Sector33Code", "Sector33CodeName"]).count()
        #多い順にsort
        df_marketcode=df_marketcode.sort_values('Code', ascending=False)
        df_marketcode=df_marketcode.reset_index()
        df_marketcode['Count']=df_marketcode['Code']
        #chart plotly
        fig = px.bar(df_marketcode, x="Sector33CodeName", y="Count", title='Number of stocks by sector')
        st.plotly_chart(fig, theme="streamlit", use_container_width=True)
    with tab3:
        st.write('Plots returns by sector for the last 3 and 6 months')
        df_p = get_price_range()
        df_p_work=df_p.copy()
        #st.dataframe(df_p_work.head())
        # 直近3ヶ月および6ヶ月のセクター別リターンをプロットします
        # データから最も古い日付を取得します
        base_date = df_p_work["Date"].min()
        # データから最新日付を取得します
        evaluation_date = df_p_work["Date"].max()
        # 6ヶ月前の日付を取得します
        base_6months_date = df_p_work.loc[df_p["Date"] <= (evaluation_date - pd.Timedelta(180, unit="D")).to_datetime64(), "Date"].max()
        # ３ヶ月前の日付を取得します
        base_3months_date = df_p_work.loc[df_p["Date"] <= (evaluation_date - pd.Timedelta(90, unit="D")).to_datetime64(), "Date"].max()
        # 取引がなかった日付の終値には0が含まれていますがそのままでは計算しずらいため
        # 終値が0の場合は前営業日の終値を使用します
        df_p_work.sort_values(["Code", "Date"], inplace=True)
        df_p_work["AdjustmentClose"].replace({0.0: np.nan}, inplace=True)
        df_p_work.loc[:, "AdjustmentClose"] = df_p_work.groupby("Code")["AdjustmentClose"].ffill()
        # 終値がnanの場合は翌営業日の終値を使用します (データの先頭をフィルするため)
        df_p_work.loc[:, "AdjustmentClose"] = df_p_work.groupby("Code")["AdjustmentClose"].bfill()
        # 基準日の株価を取得します
        filter_base_date = df_p["Date"] == base_date
        df_base = df_p_work.loc[filter_base_date]
        # 6ヶ月前の株価を取得します
        filter_6months_date = df_p_work["Date"] == base_6months_date
        df_6months = df_p_work.loc[filter_6months_date]
        # 3ヶ月前の株価を取得します
        filter_3months_date = df_p_work["Date"] == base_3months_date
        df_3months = df_p_work.loc[filter_3months_date]
        # 評価日の株価を取得します
        filter_eval_date = df_p_work["Date"] == evaluation_date
        df_eval = df_p_work.loc[filter_eval_date]
        # データを結合する際に必要なカラムを指定します
        cols = ["Code", "Date", "AdjustmentClose"]
        # 評価日の株価をベースに作業します
        df_work = df_eval[cols]
        # 基準日の株価と結合します
        df_work = pd.merge(df_work, df_base[cols], on=["Code"], how="left", suffixes=("", "_base"))
        # 6ヶ月前の株価と結合します
        df_work = pd.merge(df_work, df_6months[cols], on=["Code"], how="left", suffixes=("", "_6months"))
        # 3ヶ月前の株価と結合します
        df_work = pd.merge(df_work, df_3months[cols], on=["Code"], how="left", suffixes=("", "_3months"))
        # 6ヶ月間のリターンを算出します
        df_work["return_6months"] = ((df_work["AdjustmentClose"] / df_work["AdjustmentClose_6months"]) - 1) * 100
        # 3ヶ月間のリターンを算出します
        df_work["return_3months"] = ((df_work["AdjustmentClose"] / df_work["AdjustmentClose_3months"]) - 1) * 100
        # 月末営業日を取得します
        eoms = df_p_work.groupby(pd.Grouper(key="Date", freq="M")).apply(lambda df: df["Date"].max()).tolist()
        # 月末の株価と結合してリターンを算出します
        prev_ym = eoms[0].strftime("%Y%m")
        for i, eom in enumerate(eoms):
            ym = eom.strftime("%Y%m")
            filter_eom = df_p_work["Date"] == eom
            df = df_p_work.loc[filter_eom]
            df_work = pd.merge(df_work, df[cols], on=["Code"], how="left", suffixes=("", f"_{ym}"))
            if i != 0:
                df_work[f"return_monthly_{ym}"] = ((df_work[f"AdjustmentClose_{ym}"] / df_work[f"AdjustmentClose_{prev_ym}"]) - 1) * 100
            prev_ym = ym

        # セクター情報と結合します
        df_work = pd.merge(df_work, df_list[["Code", "Sector33Code", "Sector33CodeName", "MarketCode"]], on=["Code"])
        # プライム銘柄に絞り込みます
        df_work = df_work.loc[df_work["MarketCode"] == "111"]
        # 6ヶ月、3ヶ月、および基準日を出力します
        #st.write(base_6months_date)
        #st.write(base_3months_date)
        #st.write(evaluation_date)
        # セクター別のリターンをプロットします        
        df_work_map=df_work.groupby("Sector33CodeName")["return_6months", "return_3months"].mean().sort_values("return_6months", ascending=False)
        a_df_work_map = df_work_map.T.values
        fig3 = go.Figure(data=go.Heatmap(
                    z=a_df_work_map,
                    x=df_work_map.index,
                    y=df_work_map.columns,
                    colorscale='bluered'))
        fig3.update_layout(title='Returns by sector for the last 3 and 6 months')
        st.plotly_chart(fig3, theme="streamlit", use_container_width=True)
        
        # 月毎のリターンの項目名を取得します
        st.write('Plots monthly returns by sector')
        monthly_cols = sorted([c for c in df_work.columns if c.startswith("return_monthly_")])
        # セクター別のリターンを算出します
        df_monthly = df_work.groupby("Sector33CodeName")[monthly_cols].mean()
        a_df_monthly = df_monthly.T.values
        fig4 = go.Figure(data=go.Heatmap(
                    z=a_df_monthly,
                    x=df_monthly.index,
                    y=df_monthly.columns,
                    colorscale='bluered'))
        fig4.update_layout(title='Monthly returns by sector')
        st.plotly_chart(fig4, theme="streamlit", use_container_width=True)

#Dividend
st.header('Dividend')
st.write('List dividend yields.')
if any(dict_refresh_token):
    df_s=get_statements_range()
    df_s_work = df_s.copy()
    df_s_dividend=culc_dividend(df_s_work,df_p_work)
    st.dataframe(df_s_dividend)
    st.write('Plot the relationship as dividend yield on the horizontal axis and 1,3 month return on the vertical axis')
    col1, col2 = st.columns(2)
    with col1:
        fig_1M = px.scatter(df_s_dividend.loc[df_s_dividend["配当利回り"] > 0.00]
                , x='配当利回り', y='1ヶ月リターン', trendline="ols")
        st.plotly_chart(fig_1M, theme="streamlit", use_container_width=True)
    with col2:
        fig_3M = px.scatter(df_s_dividend.loc[df_s_dividend["配当利回り"] > 0.00]
                , x='配当利回り', y='3ヶ月リターン', trendline="ols")
        st.plotly_chart(fig_3M, theme="streamlit", use_container_width=True)
    col3, col4 = st.columns(2)
    with col3:
        fig_1M = px.scatter(df_s_dividend.loc[df_s_dividend["予想配当利回り"] > 0.00]
                , x='予想配当利回り', y='1ヶ月リターン', trendline="ols")
        st.plotly_chart(fig_1M, theme="streamlit", use_container_width=True)
    with col4:
        fig_3M = px.scatter(df_s_dividend.loc[df_s_dividend["予想配当利回り"] > 0.00]
                , x='予想配当利回り', y='3ヶ月リターン', trendline="ols")
        st.plotly_chart(fig_3M, theme="streamlit", use_container_width=True)


