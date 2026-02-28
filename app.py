import streamlit as st
import mysql.connector
import json
import sys

# Your TiDB config from secrets.toml
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

# Check for API mode (support both query_params styles)
try:
    params = st.query_params.to_dict(flat=False)
except AttributeError:
    params = st.experimental_get_query_params()

api_value = params.get("api", [None])[0]

if api_value == "get_pins":
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        result = row or {"D0":0,"D1":0,"D2":0,"D3":0,"D4":0,"D5":0,"D6":0,"D7":0,"D8":0}
        print(json.dumps(result))  # Print directly → becomes raw response body
        sys.exit(0)                # Hard exit to prevent any UI rendering
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(0)

# If not API mode → normal app UI
st.title("Medical4 Pins Control")
st.write("Normal dashboard here...")
# ... rest of your UI code
