import streamlit as st

st.title('Send mail')

with st.expander('overview'):
    st.caption('This app is a sample of creating an email in streamlit.')

st.write('Create mail!')
mailto = st.text_input('mailto', 'test@streamlit.io')
subject = st.text_input('subject', 'sample')
body = st.text_input('body', 'This email is a sample.')

mail_text = '<a href="mailto:' + mailto + \
            '?subject=' + subject + \
            '&body=' + body + \
            '">Contact me !</a>'

st.markdown(mail_text, unsafe_allow_html=True)
