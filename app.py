import streamlit as st
import mysql.connector
import json
import sys

# Your TiDB config from secrets
ti = st.secrets.tidb
db_config = {
    "host": ti.host,
    "port": ti.port,
    "user": ti.user,
    "password": ti.password,
    "database": ti.database,
    "ssl_ca": ti.ssl_ca,
    "ssl_verify_cert": True,
}

# Modern query params handling
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
        print(json.dumps(result))  # Raw output for ESP8266
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(0)

# ── Normal app UI starts here ──
st.title("Medical4 Pins Dashboard")
st.write("Welcome to the control panel...")
# ... your other widgets, buttons, etc.
