import streamlit as st
import mysql.connector
import pandas as pd
import time
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# ----------------------------
# Streamlit UI Configuration
# ----------------------------
st.set_page_config(page_title="🌍 ESP TiDB Global Control", layout="wide")
st.title("🌍 ESP8266 GLOBAL CONTROL via TiDB Cloud")

PINS = ["D0","D1","D2","D3","D4","D5","D6","D7","D8"]

# ----------------------------
# TiDB Connection (Improved)
# ----------------------------
def get_tidb_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_ca=st.secrets["tidb"]["ssl_ca"],
        autocommit=True
    )

# ----------------------------
# Database Helpers
# ----------------------------
@st.cache_data(ttl=2) # Short TTL for "live" feel
def get_latest_pins():
    try:
        conn = get_tidb_connection()
        query = "SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            # Ensure values are ints/bools
            return {p: int(df.iloc[0][p]) for p in PINS}
        return {p: 0 for p in PINS}
    except Exception as e:
        st.error(f"DB Read Error: {e}")
        return {p: 0 for p in PINS}

def write_pins_to_tidb(pins_data, source="web-ai"):
    try:
        conn = get_tidb_connection()
        cursor = conn.cursor()
        
        # Convert True/False from AI to 1/0 for SQL
        values = [1 if pins_data.get(p) in [True, 1, "true"] else 0 for p in PINS]
        values.append(source)
        
        query = f"INSERT INTO pins ({','.join(PINS)}, source) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(query, tuple(values))
        conn.close()
        return True
    except Exception as e:
        st.error(f"TiDB Write Error: {e}")
        return False

def get_esp_status():
    try:
        conn = get_tidb_connection()
        query = "SELECT last_seen FROM esp_status ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        if df.empty: return False
        
        last_seen = df.iloc[0]["last_seen"]
        # Check if last seen was within the last 30 seconds
        return (time.time() - last_seen) < 30
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
Respond ONLY with valid JSON where keys are D0 to D8 and values are boolean.
Example: {{"D0":true,"D1":false,...}}""",
        input_variables=["input"]
    )
    return prompt | llm | JsonOutputParser()

# ----------------------------
# Dashboard UI
# ----------------------------
st.info("📱 Global Control Active. ESP polls TiDB every few seconds.")

# 1. ESP Status
esp_online = get_esp_status()
status_color = "🟢" if esp_online else "🔴"
st.subheader(f"{status_color} ESP8266 Status: {'ONLINE' if esp_online else 'OFFLINE'}")

# 2. Live Status Display
current_pins = get_latest_pins()
cols = st.columns(len(PINS))
for i, pin in enumerate(PINS):
    state = bool(current_pins.get(pin, 0))
    cols[i].metric(pin, "ON" if state else "OFF")

# 3. Manual Control
st.divider()
st.subheader("🔧 Manual Control")
toggle_cols = st.columns(3)
for i, pin in enumerate(PINS):
    with toggle_cols[i%3]:
        # Use session state to avoid double-triggering
        is_on = bool(current_pins.get(pin, 0))
        if st.button(f"{'Turn OFF' if is_on else 'Turn ON'} {pin}", key=f"btn_{pin}"):
            new_pins = current_pins.copy()
            new_pins[pin] = 0 if is_on else 1
            if write_pins_to_tidb(new_pins, source="manual"):
                st.toast(f"Updated {pin}!")
                time.sleep(0.5)
                st.rerun()

# 4. AI Control
st.divider()
st.subheader("🤖 AI Smart Control")
ai_input = st.text_input("Example: 'Turn on D1 and D5, turn off everything else'")
if st.button("Execute AI Command") and ai_input:
    with st.spinner("AI Thinking..."):
        try:
            chain = setup_groq_ai()
            ai_result = chain.invoke({"input": ai_input})
            if write_pins_to_tidb(ai_result, source="AI"):
                st.success("AI Command Deployed!")
                time.sleep(1)
                st.rerun()
        except Exception as e:
            st.error(f"AI failed: {e}")

# 5. Quick Actions
st.divider()
c1, c2, c3 = st.columns(3)
if c1.button("ALL ON", use_container_width=True):
    write_pins_to_tidb({p: 1 for p in PINS}, "all_on")
    st.rerun()
if c2.button("ALL OFF", use_container_width=True):
    write_pins_to_tidb({p: 0 for p in PINS}, "all_off")
    st.rerun()
if c3.button("REFRESH", use_container_width=True):
    st.rerun()
