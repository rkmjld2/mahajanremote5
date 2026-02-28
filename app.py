import streamlit as st
import mysql.connector
import json
import mysql.connector.constants  # for ClientFlag

# ── TiDB config from secrets ──
ti = st.secrets["tidb"]

db_config = {
    "host": ti["host"],
    "port": ti["port"],
    "user": ti["user"],
    "password": ti["password"],
    "database": ti["database"],
    "ssl_ca": ti["ssl_ca"],                 # your full PEM string
    "ssl_verify_cert": True,
    "ssl_verify_identity": False,           # optional relax if hostname mismatch
    
    # Fixes for SSL_CTX_set_default_verify_paths failed
    "use_pure": True,                       # pure Python SSL → avoids C bugs
    "client_flags": [mysql.connector.constants.ClientFlag.SSL],
}

# ── API check ──
params = st.query_params
if params.get("api", [None])[0] == "get_pins":
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        result = row or {"D0":0,"D1":0,"D2":0,"D3":0,"D4":0,"D5":0,"D6":0,"D7":0,"D8":0}
        st.text(json.dumps(result))
        st.stop()
    except Exception as e:
        st.text(json.dumps({"error": str(e)}))
        st.stop()

# ── Normal dashboard ──
st.title("Medical4 Pins Dashboard")
st.write("Welcome to the control panel...")

st.subheader("Current Pin States")
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        st.json(row)
    else:
        st.info("No pins row found.")
except Exception as e:
    st.error(f"Could not read pins: {e}")

st.info("ESP8266 API URL:\nhttps://mahajanremote5.streamlit.app/?api=get_pins")
