import streamlit as st
import mysql.connector
import json
import tempfile
import os
import mysql.connector.constants
import sys  # Added for sys.exit to force hard stop in API mode

# ── TiDB config from secrets ──
ti = st.secrets["tidb"]
# Write PEM certificate to temp file (fixes previous "filename too long" issue)
with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as temp_ca_file:
    temp_ca_file.write(ti["ssl_ca"].encode('utf-8'))
    temp_ca_path = temp_ca_file.name
db_config = {
    "host": ti["host"],
    "port": ti["port"],
    "user": ti["user"],
    "password": ti["password"],
    "database": ti["database"],
    "ssl_ca": temp_ca_path,
    "ssl_verify_cert": True,
    "ssl_verify_identity": False,
    "use_pure": True,
    "client_flags": [mysql.connector.constants.ClientFlag.SSL],
}
def cleanup_temp():
    if os.path.exists(temp_ca_path):
        os.unlink(temp_ca_path)
# ── Helper function to connect and run query ──
def get_db_connection():
    return mysql.connector.connect(**db_config)

# ── API endpoint for ESP8266 (read only) ──
# Moved to the very top for priority; added print and sys.exit for robust plain JSON output
params = st.query_params
if params.get("api", [None])[0] == "get_pins":
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        result = row or {"D0":0,"D1":0,"D2":0,"D3":0,"D4":0,"D5":0,"D6":0,"D7":0,"D8":0}
        # Force plain JSON output
        print(json.dumps(result))  # For Streamlit logs/debugging
        st.text(json.dumps(result))
        st.stop()
        sys.exit(0)  # Hard exit to prevent any further Streamlit rendering/redirects
    except Exception as e:
        error_resp = json.dumps({"error": str(e)})
        print(error_resp)
        st.text(error_resp)
        st.stop()
        sys.exit(0)
    finally:
        cleanup_temp()

# ────────────────────────────────────────────────────────────────
# NORMAL DASHBOARD (web UI) ── Only runs if not API call
# ────────────────────────────────────────────────────────────────
st.title("Medical4 Pins Control Panel")
st.write("Change pin states and save to TiDB Cloud database")

# ── Read current values ──
