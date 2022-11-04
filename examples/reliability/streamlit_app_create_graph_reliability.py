import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
from lifelines import KaplanMeierFitter,NelsonAalenFitter

st.title('📉 Create a line chart of reliability')

uploaded_file = st.file_uploader("Choose a csv file")
if uploaded_file is not None:
    # Can be used wherever a "file-like" object is accepted:
    try:
        df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_csv(uploaded_file, encoding='cp932')

    #st.write('File name is ',uploaded_file.name)
    title_name=uploaded_file.name.replace('.csv','')
    with st.expander("See dataframe"):
        st.dataframe(df)
    #list
    df2=df.select_dtypes(include=[int,float, bool])
    items=list(df2.columns)
    #Select array of durations
    duration = st.radio(
        "Select a array of durations",
        items)
    #Select observed array
    items.remove(duration)
    observed = st.radio(
        "Select a either boolean or binary array representing whether the “death” was observed or not",
        items)
    #lifelines
    T = df[duration]
    E = df[observed]
    #culc kmf
    kmf = KaplanMeierFitter()
    kmf.fit(T, event_observed=E)  # or, more succinctly, kmf.fit(T, E)
    #culc naf
    naf = NelsonAalenFitter()
    naf.fit(T, event_observed=E)
    df=naf.cumulative_hazard_
    df['NA_estimate']=np.exp(-1*df['NA_estimate'])
    df=pd.merge(df,kmf.survival_function_,left_index=True,right_index=True)
    #Create chart
    title_name='Reliability Kaplan-Meier'
    fig = px.line(df, x=df.index, y='KM_estimate', title=title_name)
    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    title_name='Reliability Nelson-Aalen'
    fig = px.line(df, x=df.index, y='NA_estimate', title=title_name)
    # Plot!
    st.plotly_chart(fig, use_container_width=True)
else:
        st.info(
            f"""
                👆 Upload a .csv file first. Sample to try :[sample.csv](https://raw.githubusercontent.com/CamDavidsonPilon/lifelines/master/lifelines/datasets/waltons_dataset.csv)
                """
        )
        #read url to dataframe
        df_csv=pd.read_csv('https://raw.githubusercontent.com/CamDavidsonPilon/lifelines/master/lifelines/datasets/waltons_dataset.csv')
        #to csv
        csv = df_csv.to_csv(index=False)
        #download csv file
        st.download_button(
            label="Download sample data as CSV",
            data=csv,
            file_name='sample.csv',
            mime='text/csv',
        )
        st.stop()

