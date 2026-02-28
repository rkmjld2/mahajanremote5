import streamlit as st
import mysql.connector
import json

# ────────────────────────────────────────────────
# 1. Load TiDB connection details from secrets.toml
#    (paste your secrets in Streamlit Cloud dashboard)
# ────────────────────────────────────────────────
ti = st.secrets["tidb"]

db_config = {
    "host": ti["host"],
    "port": ti["port"],
    "user": ti["user"],
    "password": ti["password"],
    "database": ti["database"],
    "ssl_ca": ti["ssl_ca"],
    "ssl_verify_cert": True,
    "raise_on_warnings": True,
}

# ────────────────────────────────────────────────
# 2. Check if this is an API call from ESP8266
# ────────────────────────────────────────────────
params = st.query_params

# Modern & safe way — get the value of ?api=...
api_mode = params.get("api", [None])[0] == "get_pins"

if api_mode:
    # ── API MODE ── only return JSON, no dashboard
    try:
        # Connect to TiDB
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Read the pins row (assuming one row exists)
        cursor.execute("""
            SELECT D0, D1, D2, D3, D4, D5, D6, D7, D8
            FROM pins
            LIMIT 1
        """)

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        # If no row → return zeros
        result = row if row else {
            "D0": 0, "D1": 0, "D2": 0, "D3": 0,
            "D4": 0, "D5": 0, "D6": 0, "D7": 0, "D8": 0
        }

        # Output pure JSON
        st.text(json.dumps(result))

        # Stop here — do NOT render dashboard
        st.stop()

    except Exception as e:
        error_result = {"error": str(e)}
        st.text(json.dumps(error_result))
        st.stop()

# ────────────────────────────────────────────────
# 3. Normal dashboard (only shown when NOT in API mode)
# ────────────────────────────────────────────────

st.title("Medical4 Pins Dashboard")
st.write("Welcome to the control panel...")

st.markdown("---")

st.subheader("Current pin states from database")

# Optional: show current pins in the dashboard too
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row:
        st.json(row)  # nice formatted view in dashboard
    else:
        st.info("No pins row found in database.")

except Exception as e:
    st.error(f"Could not read pins: {e}")

st.markdown("---")

st.info("Use this URL for ESP8266:  \nhttps://your-app-name.streamlit.app/?api=get_pins")

# You can add more controls here later (buttons to change pins, etc.)
# Example:
# if st.button("Turn all ON"):
#     # update database code here...
