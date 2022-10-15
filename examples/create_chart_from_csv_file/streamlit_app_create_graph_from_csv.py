import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px

st.title('📉 Create a line chart')

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
    #Select x axis
    chart_x_axis = st.radio(
        "Select x-axis",
        df.columns)
    #st.write('You selected:', chart_x_axis)
    #Select y axis
    list_y_axis=list(df.columns)
    list_y_axis.remove(chart_x_axis)
    chart_y_axis = st.multiselect(
        'Select y-axis',
        list_y_axis,
        list_y_axis[0])
    #st.write('You selected:', chart_y_axis)

    #Create chart
    fig = px.line(df, x=chart_x_axis, y=chart_y_axis, title=title_name)
    # Plot!
    st.plotly_chart(fig, use_container_width=True)
else:
        st.info(
            f"""
                👆 Upload a .csv file first. Sample to try :[sample.csv](https://github.com/stemtazoo/streamlit_app/blob/main/examples/create_chart_from_csv_file/sample.csv)
                """
        )
        #data sample.csv
        x=np.arange(0,360,2)
        y_1=np.sin(np.radians(x))
        y_2=np.sin(np.radians(2*x))
        y_3=np.sin(np.radians(3*x))
        s_x=pd.Series(x)
        s_y_1=pd.Series(y_1)
        s_y_2=pd.Series(y_2)
        s_y_3=pd.Series(y_3)
        df_csv=pd.concat([s_x,s_y_1,s_y_2,s_y_3],axis=1)
        df_csv.columns=['x','y_1','y_2','y_3']
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

