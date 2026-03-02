import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# ────────────────────────────────────────────────
#  Your existing TiDB connection (from secrets.toml)
# ────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    # Example using st.secrets (recommended)
    db_url = (
        f"mysql+mysqlconnector://"
        f"{st.secrets['tidb']['username']}:{st.secrets['tidb']['password']}"
        f"@{st.secrets['tidb']['host']}:{st.secrets['tidb']['port']}/"
        f"{st.secrets['tidb']['database']}?ssl_ca={st.secrets['tidb'].get('ssl_ca', '')}"
    )
    engine = create_engine(db_url)
    return engine

# ────────────────────────────────────────────────
#  Public API endpoint: /api/get_pins
#  → anyone can call this (no auth for simplicity)
# ────────────────────────────────────────────────
if "api" in st.query_params:   # or use st.experimental_get_query_params() in older versions
    if st.query_params["api"][0] == "get_pins":
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
                # Convert int → str for clean JSON (like your old PHP)
                row = {k: str(v) for k, v in row.items()}
                st.json(row)
            else:
                st.json({"error": "No records found"})
                
        except Exception as e:
            st.json({"error": str(e)})
        st.stop()   # Important: stop normal app render

# ────────────────────────────────────────────────
#  Your normal Streamlit app continues below...
#  e.g. st.title("My Medical App"), forms, charts etc.
# ────────────────────────────────────────────────
st.title("Welcome to Medical4 App")
# ... rest of your app ...
