import streamlit as st
import mysql.connector
import json
import tempfile
import os
import mysql.connector.constants

# ── TiDB config from secrets ──
ti = st.secrets["tidb"]

# Write PEM certificate to temp file
with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as temp_ca_file:
    temp_ca_file.write(ti["ssl_ca"].encode("utf-8"))
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

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ─────────────────────────────────────────
# ✅ API ENDPOINT (FOR ESP8266)
# ─────────────────────────────────────────
params = st.query_params

if params.get("api") == "get_pins":
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        result = row or {
            "D0":0,"D1":0,"D2":0,"D3":0,"D4":0,
            "D5":0,"D6":0,"D7":0,"D8":0
        }

        st.write(json.dumps(result))
        st.stop()

    except Exception as e:
        st.write(json.dumps({"error": str(e)}))
        st.stop()

    finally:
        cleanup_temp()

# ─────────────────────────────────────────
# 🖥️ NORMAL DASHBOARD UI
# ─────────────────────────────────────────

st.title("Medical4 Pins Control Panel")
st.write("Change pin states and save to TiDB Cloud database")

current_pins = {
    "D0":0,"D1":0,"D2":0,"D3":0,"D4":0,
    "D5":0,"D6":0,"D7":0,"D8":0
}

try:
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
    row = cursor.fetchone()
    if row:
        current_pins = row
    cursor.close()
    conn.close()
except Exception as e:
    st.error(f"Could not load current pins: {e}")

st.subheader("Current Pin States")
st.json(current_pins)

st.subheader("Update Pin States")

with st.form("update_pins_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        d0 = st.checkbox("D0", value=bool(current_pins["D0"]))
        d1 = st.checkbox("D1", value=bool(current_pins["D1"]))
        d2 = st.checkbox("D2", value=bool(current_pins["D2"]))

    with col2:
        d3 = st.checkbox("D3", value=bool(current_pins["D3"]))
        d4 = st.checkbox("D4", value=bool(current_pins["D4"]))
        d5 = st.checkbox("D5", value=bool(current_pins["D5"]))

    with col3:
        d6 = st.checkbox("D6", value=bool(current_pins["D6"]))
        d7 = st.checkbox("D7", value=bool(current_pins["D7"]))
        d8 = st.checkbox("D8", value=bool(current_pins["D8"]))

    submitted = st.form_submit_button("Save to Database")

    if submitted:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            query = """
                UPDATE pins
                SET
                    D0=%s,D1=%s,D2=%s,
                    D3=%s,D4=%s,D5=%s,
                    D6=%s,D7=%s,D8=%s
                LIMIT 1
            """

            values = (
                int(d0), int(d1), int(d2),
                int(d3), int(d4), int(d5),
                int(d6), int(d7), int(d8)
            )

            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            conn.close()

            st.success("Pins updated successfully!")
            st.rerun()

        except Exception as e:
            st.error(f"Update failed: {e}")

        finally:
            cleanup_temp()

st.markdown("---")
st.info("ESP8266 API:\nhttps://mahajanremote5.streamlit.app/?api=get_pins")
