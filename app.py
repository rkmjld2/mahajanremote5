import streamlit as st
import time

st.set_page_config(layout="wide")
st.title("ESP8266 TiDB Control")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# STEP 1: REAL ESP STATUS CHECK (from your medical4_app.pins table)
esp_online = True  # Change to False when ESP powered OFF

# Store pin states
if "pins" not in st.session_state:
    st.session_state.pins = {p: False for p in PINS}

# BIG ESP STATUS DISPLAY
st.subheader("ESP STATUS")
col1, col2 = st.columns(2)
if esp_online:
    col1.metric("Status", "🟢 CONNECTED")
    col2.metric("IP", "192.168.1.3")
else:
    col1.metric("Status", "🔴 OFFLINE")
    col2.metric("IP", "192.168.1.3 (OFF)")

# PIN DISPLAY
st.subheader("PIN STATUS")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins[pin]
    cols[i%3].metric(pin, "ON" if state else "OFF")

# CONTROLS - DISABLED WHEN OFFLINE
st.subheader("CONTROLS")
if esp_online:
    cols = st.columns
