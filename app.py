import streamlit as st
import pandas as pd
from sqlalchemy import text

# ────────────────────────────────────────────────
# Use st.connection (preferred modern way)
# ────────────────────────────────────────────────
@st.cache_resource
def get_connection():
    return st.connection("tidb", type="sql")


conn = get_connection()


# ────────────────────────────────────────────────
# Public API endpoint: ?api=get_pins
# ────────────────────────────────────────────────
if "api" in st.query_params and st.query_params["api"][0] == "get_pins":
    try:
        query = """
            SELECT D0, D1, D2, D3, D4, D5, D6, D7, D8
            FROM pins
            ORDER BY id DESC
            LIMIT 1
        """
        
        df = conn.query(query, ttl=60)  # cache 60 seconds – adjust as needed
        
        if not df.empty:
            row = df.iloc[0].to_dict()
            # Convert to string (like your old PHP output)
            row = {k: str(v) if v is not None else None for k, v in row.items()}
            st.json(row)
        else:
            st.json({"error": "No records found in pins table"})
            
    except Exception as e:
        st.json({"error": f"Server error: {str(e)}"})
    
    st.stop()  # Stop rendering the normal UI


# ────────────────────────────────────────────────
# Normal Streamlit app
# ────────────────────────────────────────────────
st.title("Welcome to Medical4 App")

with st.expander("Debug Info", expanded=False):
    st.write("Streamlit version:", st.__version__)
    if "tidb" in st.secrets.get("connections", {}):
        st.success("TiDB connection config found")
    else:
        st.warning("TiDB connection config missing – check secrets")


if st.button("Show latest pin record"):
    try:
        query = """
            SELECT D0, D1, D2, D3, D4, D5, D6, D7, D8
            FROM pins
            ORDER BY id DESC
            LIMIT 1
        """
        df = conn.query(query)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No records in pins table")
    except Exception as e:
        st.error(f"Database error: {str(e)}")

# ... rest of your app (forms, charts, login, etc.) ...
