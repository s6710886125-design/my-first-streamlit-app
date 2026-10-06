import streamlit as st

st.title("My First Streamlit App")
name = st.text_input("Enter your name")
if name:
    st.write(f"สวัสดี {name}! แอปนี้ Deploy สำเร็จแล้ว 🎉")