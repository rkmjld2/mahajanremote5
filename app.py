import streamlit as st
import mysql.connector
import pandas as pd
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# --- Page Configuration ---
st.set_page_config(page_title="ESP8266 Global Control", layout="wide")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# --- Database Connection using Secrets ---
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        autocommit=True
    )

def send_command(pin_values, source="manual"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Prepare SQL for the exact fields in your 'pins' table
        columns = ", ".join(PINS + ["source"])
        placeholders = ", ".join(["%s"] * (len(PINS) + 1))
        
        # Convert inputs to 1s and 0s
        data = [1 if pin_values.get(p) in [True, 1, "on", "ON"] else 0 for p in PINS]
        data.append(source)
        
        sql = f"INSERT INTO pins ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, tuple(data))
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Write Error: {e}")
        return False

def get_current_status():
    try:
        conn = get_db_connection()
        query = "SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else {p: 0 for p in PINS}
    except:
        return {p: 0 for p in PINS}

# --- UI Dashboard ---
st.title("🌍 ESP8266 Global Control Dashboard")
current_state = get_current_status()

# AI Control Section (Credentials hidden in Secrets)
st.subheader("🤖 AI Smart Control")
ai_input = st.text_input("Voice/Text Command:", placeholder="e.g., 'Turn on D0 and D4, turn off others'")

if st.button("🚀 Send AI Command") and ai_input:
    try:
        # PULLING API KEY FROM SECRETS
        llm = ChatGroq(
            groq_api_key=st.secrets["groq"]["api_key"],
            model_name="mixtral-8x7b-32768",
            temperature=0
        )
        
        parser = JsonOutputParser()
        prompt = PromptTemplate(
            template="You control ESP8266 pins D0-D8. Command: {input}. Respond ONLY with valid JSON keys D0-D8 with values 1 (on) or 0 (off).",
            input_variables=["input"]
        )
        
        chain = prompt | llm | parser
        ai_res = chain.invoke({"input": ai_input})
        
        if send_command(ai_res, source="AI"):
            st.success("AI Command stored in TiDB!")
            st.rerun()
    except Exception as e:
        st.error(f"AI Error: {e}")

st.divider()

# Status Display
cols = st.columns(9)
for i, p in enumerate(PINS):
    status = "🟢 ON" if current_state.get(p) == 1 else "🔴 OFF"
    cols[i].metric(p, status)

# Manual Controls
st.subheader("🔧 Manual Pin Toggles")
m_cols = st.columns(3)
for i, p in enumerate(PINS):
    with m_cols[i%3]:
        if st.button(f"Switch {p}", key=f"btn_{p}"):
            new_val = 0 if current_state.get(p) == 1 else 1
            cmd = current_state.copy()
            cmd[p] = new_val
            if send_command(cmd, source="Manual Web"):
                st.rerun()

if st.button("⚠️ ALL OFF", type="primary", use_container_width=True):
    send_command({p: 0 for p in PINS}, source="Emergency Stop")
    st.rerun()
