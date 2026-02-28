import streamlit as st
import pandas as pd
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP TiDB Global Control")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# TiDB Direct (no langchain - pure pymysql)
@st.cache_data(ttl=5)
def get_pins():
    import pymysql
    try:
        conn = pymysql.connect(
            host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
            port=4000,
            user="ax6KHc1BNkyuaor.root",
            password="EP8isIWoEOQk7DSr",
            database="medical4_app"
        )
        df = pd.read_sql("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM esp_pins ORDER BY id DESC LIMIT 1", conn)
        conn.close()
        return dict(df.iloc[0]) if not df.empty else {p: False for p in PINS}
    except:
        return {p: False for p: False for p in PINS}

def set_pins(pins):
    import pymysql
    conn = pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="ax6KHc1BNkyuaor.root", 
        password="EP8isIWoEOQk7DSr",
        database="medical4_app"
    )
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO esp_pins (D0,D1,D2,D3,D4,D5,D6,D7,D8) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", tuple(pins.values()))
        conn.commit()
    conn.close()
    st.success("✅ ESP COMMAND SENT!")

if "pins" not in st.session_state:
    st.session_state.pins = get_pins()

pins = get_pins()
st.session_state.pins = pins

# DISPLAY
st.subheader("📊 PINS")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    cols[i%3].metric(pin, "🟢 ON" if pins[pin] else "🔴 OFF")

# CONTROLS  
st.subheader("🔧 CONTROL")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    with cols[i%3]:
        if st.button(f"{pin} {'ON' if not pins[pin] else 'OFF'}", key=pin):
            pins[pin] = not pins[pin]
            set_pins(pins)
            st.rerun()

if st.button("🌟 ALL ON", type="primary"):
    all_on = {p: True for p in PINS}
    set_pins(all_on)
    st.rerun()

if st.button("💤 ALL OFF"):
    all_off = {p: False for p in PINS}
    set_pins(all_off) 
    st.rerun()

st.success("🌍 Works from USA mobile data → ESP India!")
