import streamlit as st
import pymysql
import pandas as pd
import time
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

st.set_page_config(page_title="🌍 ESP TiDB Global Control", layout="wide")
st.title("🌍 ESP8266 GLOBAL CONTROL via TiDB Cloud")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

@st.cache_resource
def get_tidb():
    return pymysql.connect(
        host="gateway01.ap-southeast-1.prod.aws.tidbcloud.com",
        port=4000,
        user="ax6KHc1BNkyuaor.root",
        password="EP8isIWoEOQk7DSr",
        database="medical4_app",
        ssl={'ca': st.secrets["tidb_ssl_ca"]}
    )

@st.cache_data(ttl=5)
def get_pins():
    conn = get_tidb()
    df = pd.read_sql("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM esp_pins ORDER BY id DESC LIMIT 1", conn)
    conn.close()
    return dict(df.iloc[0]) if not df.empty else {p: False for p in PINS}

def set_pins(pins):
    conn = get_tidb()
    with conn.cursor() as cursor:
        cursor.execute("INSERT INTO esp_pins (D0,D1,D2,D3,D4,D5,D6,D7,D8, command_from) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'web')", tuple(pins.values()))
        conn.commit()
    conn.close()
    st.success("✅ Commands sent to ESP!")

# AI Setup
@st.cache_resource
def get_ai():
    llm = ChatGroq(groq_api_key=st.secrets["groq_api_key"], model_name="mixtral-8x7b-32768")
    prompt = PromptTemplate(template='ESP D0-D8. "{input}" → {{"D0":0/1,"D1":0/1,"D2":0/1,"D3":0/1,"D4":0/1,"D5":0/1,"D6":0/1,"D7":0/1,"D8":0/1}}', input_variables=["input"])
    return prompt | llm | JsonOutputParser()

if "pins" not in st.session_state:
    st.session_state.pins = get_pins()

st.success("🌍 GLOBAL CONTROL LIVE!")
pins = get_pins()
st.session_state.pins = pins

# PINS DISPLAY
st.subheader("📊 PINS STATUS")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    cols[i%3].metric(pin, "🟢 ON" if st.session_state.pins[pin] else "🔴 OFF")

# CONTROLS
st.subheader("🔧 CONTROL")
toggle_cols = st.columns(3)
for i, pin in enumerate(PINS):
    with toggle_cols[i%3]:
        new_state = st.checkbox(pin, st.session_state.pins[pin], key=pin)
        if new_state != st.session_state.pins[pin]:
            st.session_state.pins[pin] = new_state
            set_pins(st.session_state.pins)
            st.rerun()

col1, col2 = st.columns([3,1])
with col1:
    cmd = st.text_input("AI: 'D1 on', 'all off'")
with col2:
    if st.button("AI ►") and cmd:
        ai_pins = get_ai().invoke({"input": cmd})
        set_pins(ai_pins)
        st.session_state.pins = ai_pins
        st.rerun()

st.columns(3)[0].button("🌟 ALL ON", on_click=lambda: [set_pins({p:True for p in PINS}), setattr(st.session_state, 'pins', {p:True for p in PINS}), st.rerun()])
st.columns(3)[1].button("💤 ALL OFF", on_click=lambda: [set_pins({p:False for p in PINS}), setattr(st.session_state, 'pins', {p:False for p in PINS}), st.rerun()])
