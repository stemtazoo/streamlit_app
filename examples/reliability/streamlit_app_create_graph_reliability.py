import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
from lifelines import KaplanMeierFitter,NelsonAalenFitter

#panda dataframe columns 01 to bool
def columns_tobool(df): 
    length=len(df)
    for column in df.columns:
        if len(df[(df[column]==0)|(df[column]==1)])==length:
            df[column] = df[column].astype(bool) 
    return df 

#Reliability estimate
def reliability_estimate(df,duration,observed):
    T = df[duration]
    E = df[observed]
    #culc kmf
    kmf = KaplanMeierFitter()
    kmf.fit(T, event_observed=E)  # or, more succinctly, kmf.fit(T, E)
    df_kmf=kmf.survival_function_
    df_kmf['model']='KaplanMeierFitter'
    df_kmf=df_kmf.rename(columns={'KM_estimate': 'reliability'})
    #culc naf
    naf = NelsonAalenFitter()
    naf.fit(T, event_observed=E)
    df_naf=naf.cumulative_hazard_
    df_naf['reliability']=np.exp(-1*df_naf['NA_estimate'])
    df_naf['model']='NelsonAalenFitter'
    df_reliability=pd.concat([df_kmf,df_naf])
    return df_reliability

st.title('📉 Create a line chart of reliability')

uploaded_file = st.file_uploader("Choose a csv file")
if uploaded_file is not None:
    # Can be used wherever a "file-like" object is accepted:
    try:
        df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_csv(uploaded_file, encoding='cp932')

    #dataframe column 01 to bool
    df=columns_tobool(df)
    #st.write('File name is ',uploaded_file.name)
    title_name=uploaded_file.name.replace('.csv','')
    with st.expander("See dataframe"):
        st.dataframe(df)
    #list
    df2=df.select_dtypes(include=[int,float])
    items=list(df2.columns)
    #Select array of durations
    duration = st.radio(
        "Select a array of durations",
        items)
    #Select observed array
    df2=df.select_dtypes(include=[bool])
    items=list(df2.columns)
    observed = st.radio(
        "Select a either boolean or binary array representing whether the “death” was observed or not",
        items)
    #Select group
    items=list(df.columns)
    items.remove(duration)
    items.remove(observed)
    items.insert(0,'None')
    group = st.selectbox(
    'If using Multiple group, please select columns.',
    items)
    #lifelines
    if group != 'None':
        names=df[group].unique().tolist()
        df_reliability=pd.DataFrame()
        for name in names:
            df3=reliability_estimate(df[df[group]==name],duration,observed)
            df3['name']=name
            df_reliability=pd.concat([df_reliability,df3])
        #Create chart
        title_name='Reliability'
        df_reliability=df_reliability[df_reliability['model']=='NelsonAalenFitter']
        fig = px.line(df_reliability, x=df_reliability.index, y='reliability',color='name', title=title_name)
    else:
        df_reliability=reliability_estimate(df,duration,observed)
        #Create chart
        title_name='Reliability'
        fig = px.line(df_reliability, x=df_reliability.index, y='reliability',color='model', title=title_name)
       
    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    #show dataframe
    with st.expander("See dataframe"):
        st.dataframe(df_reliability)
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

