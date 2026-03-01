import streamlit as st
import mysql.connector
import json
import tempfile
import os
import mysql.connector.constants

# TiDB config from secrets
ti = st.secrets["tidb"]

# Write PEM certificate to temp file
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

# API endpoint for ESP8266 (read only)
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
