import streamlit as st
import mysql.connector
import json
import tempfile
import os
import mysql.connector.constants

# ── TiDB config from secrets ──
ti = st.secrets["tidb"]

# Write the PEM string to a temporary file (fixes "filename too long" error)
with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as temp_ca_file:
    temp_ca_file.write(ti["ssl_ca"].encode('utf-8'))  # write the multi-line string as bytes
    temp_ca_path = temp_ca_file.name

db_config = {
    "host": ti["host"],
    "port": ti["port"],
    "user": ti["user"],
    "password": ti["password"],
    "database": ti["database"],
    
    "ssl_ca": temp_ca_path,                 # ← now a real short file path
    "ssl_verify_cert": True,
    "ssl_verify_identity": False,           # optional: relax if hostname issues
    
    "use_pure": True,                       # pure Python → helps with SSL quirks
    "client_flags": [mysql.connector.constants.ClientFlag.SSL],
}

# Clean up temp file after use (optional but good practice)
def cleanup_temp():
    if os.path.exists(temp_ca_path):
        os.unlink(temp_ca_path)

# ── API mode for ESP8266 ──
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
    finally:
        cleanup_temp()

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
        st.info("No pins row found in table.")
except Exception as e:
    st.error(f"Could not read pins: {e}")
finally:
    cleanup_temp()

st.info("ESP8266 API URL:\nhttps://mahajanremote5.streamlit.app/?api=get_pins")
