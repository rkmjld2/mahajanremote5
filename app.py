import streamlit as st
import mysql.connector
import pandas as pd
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

# ----------------------------
# 1. Database & Security Setup
# ----------------------------
# Ensure your .streamlit/secrets.toml has [tidb] and [groq] sections
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        autocommit=True
    )

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# ----------------------------
# 2. Logic Functions
# ----------------------------
def save_to_tidb(pin_states, source="manual"):
    """Inserts a new row into your pins table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on your table schema
        cols = ", ".join(PINS + ["source"])
        placeholders = ", ".join(["%s"] * (len(PINS) + 1))
        
        # Prepare data (convert True/False to 1/0)
        values = [1 if pin_states.get(p) in [True, 1, "1"] else 0 for p in PINS]
        values.append(source)
        
        query = f"INSERT INTO pins ({cols}) VALUES ({placeholders})"
        cursor.execute(query, tuple(values))
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Write Error: {e}")
        return False

def get_latest_state():
    """Reads the most recent row from TiDB"""
    try:
        conn = get_db_connection()
        query = "SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins ORDER BY id DESC LIMIT 1"
        df = pd.read_sql(query, conn)
        conn.close()
        return df.iloc[0].to_dict() if not df.empty else {p: 0 for p in PINS}
    except:
        return {p: 0 for p in PINS}

# ----------------------------
# 3. Streamlit UI Dashboard
# ----------------------------
st.title("🌍 Medical4 ESP8266 Global Control")

# Get current status from DB
current_status = get_latest_state()

# --- AI COMMAND SECTION ---
st.subheader("🤖 AI Smart Control")
user_prompt = st.text_input("Tell the AI what to do:", placeholder="e.g. 'Turn on D1 and D2, turn off everything else'")

if st.button("Execute AI Command") and user_prompt:
    with st.spinner("AI is thinking..."):
        llm = ChatGroq(
            groq_api_key=st.secrets["groq"]["api_key"],
            model_name="mixtral-8x7b-32768"
        )
        prompt = PromptTemplate(
            template="You are a hardware controller. Command: {input}. Respond ONLY with JSON keys D0-D8 and values 1 or 0.",
            input_variables=["input"]
        )
        chain = prompt | llm | JsonOutputParser()
        
        try:
            ai_output = chain.invoke({"input": user_prompt})
            if save_to_tidb(ai_output, source="AI"):
                st.success("AI Command Deployed!")
                st.rerun()
        except Exception as e:
            st.error(f"AI Failed: {e}")

st.divider()

# --- MANUAL CONTROL SECTION ---
st.subheader("🔧 Manual Pin Control")
cols = st.columns(3)
for i, p in enumerate(PINS):
    with cols[i % 3]:
        is_on = current_status.get(p) == 1
        label = f"{p}: {'ON' if is_on else 'OFF'}"
        if st.button(f"Toggle {label}", key=f"btn_{p}"):
            # Create a new state based on current + toggle
            new_state = current_status.copy()
            new_state[p] = 0 if is_on else 1
            save_to_tidb(new_state, source="Web Toggle")
            st.rerun()

if st.button("🚨 EMERGENCY ALL OFF", type="primary", use_container_width=True):
    save_to_tidb({p: 0 for p in PINS}, source="Emergency")
    st.rerun()
