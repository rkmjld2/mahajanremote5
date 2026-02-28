import streamlit as st
import time

st.title("🚀 Streamlit Cloud Test")

if st.button("Click Me"):
    st.success("✅ Button clicked!")

st.write("⏱ Current time:", time.strftime("%Y-%m-%d %H:%M:%S"))
