import streamlit as st
import mysql.connector
import pandas as pd
import time
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from streamlit.web import cli as stcli
from flask import Flask, request, jsonify

# ----------------------------
# Streamlit UI Configuration
# ----------------------------
st.set_page_config(page_title="🌍 ESP TiDB Global Control", layout="wide")
st.title("🌍 ESP8266 GLOBAL CONTROL via TiDB Cloud")

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7","D8"]

# ----------------------------
# TiDB Connection
# ----------------------------
@st.cache_resource
def get_tidb_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_ca=st.secrets["tidb"]["ssl_ca"]
    )

# ----------------------------
# Database Helpers
# ----------------------------
@st.cache_data(ttl=5)
def get_latest_pins():
    try:
        conn = get_tidb_connection()
        query = "SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8, updated_at FROM pins ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        return dict(df.iloc[0]) if not df.empty else {p: 0 for p in PINS}
    except:
        return {p: 0 for p in PINS}

def write_pins_to_tidb(pins_data, source="web-ai"):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        query = """
        INSERT INTO pins (D0,D1,D2,D3,D4,D5,D6,D7,D8, source)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(query, (
            int(pins_data["D0"]), int(pins_data["D1"]), int(pins_data["D2"]),
            int(pins_data["D3"]), int(pins_data["D4"]), int(pins_data["D5"]),
            int(pins_data["D6"]), int(pins_data["D7"]), int(pins_data["D8"]),
            source
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"TiDB Error: {e}")
        return False

def get_esp_status():
    try:
        conn = get_tidb_connection()
        query = "SELECT last_seen FROM esp_status ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        if df.empty:
            return False
        last_seen = df.iloc[0]["last_seen"]
        return (time.time() - last_seen) < 20
    except:
        return False

# ----------------------------
# AI Command Setup
# ----------------------------
@st.cache_resource
def setup_groq_ai():
    llm = ChatGroq(
        groq_api_key=st.secrets["groq"]["api_key"],
        model_name="mixtral-8x7b-32768",
        temperature=0
    )
    prompt = PromptTemplate(
        template="""ESP8266 pins D0-D8 control. User command: "{input}"
Respond ONLY with valid JSON: {{"D0":true/false,"D1":true/false,"D2":true/false,"D3":true/false,"D4":true/false,"D5":true/false,"D6":true/false,"D7":true/false,"D8":true/false}}
Examples: "D1 on" → D1:true, "all off" → all:false""",
        input_variables=["input"]
    )
    return prompt | llm | JsonOutputParser()

# ----------------------------
# Session State
# ----------------------------
if "pins" not in st.session_state:
    st.session_state.pins = {p: 0 for p in PINS}

# ----------------------------
# Dashboard UI
# ----------------------------
st.success("🌍 **GLOBAL CONTROL** - Works from ANYWHERE in world!")
st.info("📱 Phone on mobile data → Toggle → ESP executes in 10-20s")

# ESP Status
esp_online = get_esp_status()
st.subheader("📡 ESP8266 STATUS")
if esp_online:
    st.success("🟢 ESP8266 ONLINE")
else:
    st.error("🔴 ESP8266 OFFLINE")
    for pin in PINS:
        st.session_state.pins[pin] = 0

# Live Pins
pins_data = get_latest_pins()
st.session_state.pins = pins_data
st.subheader("📊 LIVE PINS STATUS (TiDB Cloud)")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = bool(st.session_state.pins.get(pin, 0))
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

# Manual Toggles
st.subheader("🔧 MANUAL PIN CONTROL")
toggle_cols = st.columns(3)
for i, pin in enumerate(PINS):
    with toggle_cols[i%3]:
        current = bool(st.session_state.pins[pin])
        new_state = st.checkbox(f"**{pin}**", value=current, key=f"toggle_{pin}")
        if new_state != current:
            st.session_state.pins[pin] = int(new_state)
            if write_pins_to_tidb(st.session_state.pins):
                st.success(f"✅ {pin} → {'ON' if new_state else 'OFF'}")
                time.sleep(1)
                st.rerun()

# AI Commands
st.subheader("🤖 AI SMART CONTROL")
col1, col2 = st.columns([3, 1])
with col1:
    ai_command = st.text_input("Type commands like: 'D1 on', 'all off'", placeholder="turn kitchen lights on")
with col2:
    if st.button("🚀 SEND AI COMMAND", type="primary", disabled=not ai_command):
        with st.spinner("🤖 GROQ AI processing..."):
            try:
                chain = setup_groq_ai()
                ai_result = chain.invoke({"input": ai_command})
                if write_pins_to_tidb(ai_result):
                    st.session_state.pins = ai_result
                    st.success("✅ AI command sent to ESP!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"AI Error: {e}")

# Quick Actions
st.subheader("⚡ QUICK ACTIONS")
qcol1, qcol2, qcol3 = st.columns(3)
if qcol1.button("🌟 ALL ON", type="primary", use_container_width=True):
    all_on = {p: 1 for p in PINS}
    write_pins_to_tidb(all_on)
    st.session_state.pins = all_on
    st.rerun()
if qcol2.button("💤 ALL OFF", type="secondary", use_container_width=True):
    all_off = {p: 0 for p in PINS}
    write_pins_to_tidb(all_off)
    st.session_state.pins = all_off
    st.rerun()
if qcol3.button("🔄 REFRESH STATUS", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Summary
st.subheader("📈 STATUS SUMMARY")
col1, col2, col3 = st.columns(3)
on_count = sum(int(v) for v in st.session_state.pins.values())
col1.metric("🟢 PINS ON", on_count)
col2.metric("🔴 PINS OFF", 9 - on_count)
col3.metric("📡 Source", "TiDB Cloud")

st.markdown("---")
st.info("""
**🌍 GLOBAL CONTROL FLOW:**
1. ✅ You click/toggle → INSTANT write to TiDB Cloud
2. ✅ ESP polls Streamlit Cloud → Executes command
3. ✅ ESP confirms → Status updates on web instantly
4. ✅ Works from mobile data, abroad, anywhere!
""")

# ----------------------------
# REST Endpoints for ESP8266
# ----------------------------
app = Flask(__name__)

@app.route("/read_pins", methods=["GET"])
def read_pins():
    pins = get_latest_pins()
    return jsonify({"pins": pins})

@app.route("/update_status", methods=["POST"])
def update_status():
    last_seen = int(time.time())
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO esp_status (last_seen, source) VALUES (%s,%s)", (last_seen,"esp8266"))
        conn.commit()
        conn.close()
    except:
        pass
    return jsonify({"status":"online","last_seen":last_seen})

if __name__ == "__main__":
    import sys
    if st._is_running_with_streamlit:
        stcli.main()
    else:
        app.run(host="0.0
