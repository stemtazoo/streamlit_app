from lib2to3.pgen2.pgen import DFAState
from unicodedata import name
import streamlit as st
import pandas as pd
import plotly.express as px

st.title('📉　CSVファイルを読み込んで、グラフを表示する')
st.write('## ファイルを読み込む。')
uploaded_file = st.file_uploader("Choose a csv file")
if uploaded_file is not None:
    # Can be used wherever a "file-like" object is accepted:
    try:
        df = pd.read_csv(uploaded_file)
    except:
        df = pd.read_csv(uploaded_file, encoding='cp932')

    st.write('File name is ',uploaded_file.name)
    title_name=uploaded_file.name.replace('.csv','')
    st.write(df)
    #Select x axis
    chart_x_axis = st.radio(
        "Select x-axis",
        df.columns)
    st.write('You selected:', chart_x_axis)
    #Select y axis
    chart_y_axis = st.multiselect(
        'Select y-axis',
        df.columns,
        df.columns[1])
    st.write('You selected:', chart_y_axis)

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
        st.stop()

