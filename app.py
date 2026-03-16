import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# ────────────────────────────────────────────────
# TiDB connection (cached)
# ────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    try:
        # Build connection URL
        secrets = st.secrets["tidb"]
        db_url = (
            f"mysql+mysqlconnector://"
            f"{secrets['username']}:{secrets['password']}"
            f"@{secrets['host']}:{secrets['port']}/"
            f"{secrets['database']}"
            f"?charset=utf8mb4&ssl_ca={secrets.get('ssl_ca', '')}"
        )
        engine = create_engine(db_url, connect_args={"connect_timeout": 10})
        # Quick test connection on first creation
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return engine
    except Exception as e:
        st.error(f"Failed to create database connection: {str(e)}")
        st.stop()


# ────────────────────────────────────────────────
# Public API endpoint: ?api=get_pins
# ────────────────────────────────────────────────
if "api" in st.query_params and st.query_params["api"][0] == "get_pins":
    try:
        engine = get_db_connection()
        
        query = text("""
            SELECT D0, D1, D2, D3, D4, D5, D6, D7, D8
            FROM pins
            ORDER BY id DESC
            LIMIT 1
        """)
        
        df = pd.read_sql(query, engine)
        
        if not df.empty:
            row = df.iloc[0].to_dict()
            # Convert everything to string (consistent with your old PHP behavior)
            row = {k: str(v) if v is not None else None for k, v in row.items()}
            st.json(row)
        else:
            st.json({"error": "No records found in pins table"})
            
    except Exception as e:
        st.json({"error": f"Server error: {str(e)}"})
    
    st.stop()  # Prevent normal app from rendering


# ────────────────────────────────────────────────
# Normal Streamlit app (only reached if not API call)
# ────────────────────────────────────────────────
st.title("Welcome to Medical4 App")

# ── Add some debug / status info (remove later if you want clean UI) ──
with st.expander("Debug Info", expanded=False):
    st.write("Streamlit version:", st.__version__)
    if "tidb" in st.secrets:
        st.success("TiDB secrets found")
    else:
        st.warning("TiDB secrets section not found in secrets.toml")

# Example: show last pin if you want (optional)
if st.button("Show latest pin record"):
    try:
        engine = get_db_connection()
        query = text("""
            SELECT D0, D1, D2, D3, D4, D5, D6, D7, D8
            FROM pins
            ORDER BY id DESC
            LIMIT 1
        """)
        df = pd.read_sql(query, engine)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No records in pins table")
    except Exception as e:
        st.error(f"Database error: {str(e)}")

# ... rest of your app (forms, charts, login, etc.) ...
