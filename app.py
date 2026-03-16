import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import os

# ────────────────────────────────────────────────
# TiDB connection (cached – production-safe with embedded cert)
# ────────────────────────────────────────────────
@st.cache_resource
def get_db_connection():
    try:
        secrets = st.secrets["tidb"]
        
        # Get embedded CA certificate content (multi-line string from secrets.toml)
        ca_content = secrets.get("ca_cert", "")
        if not ca_content:
            raise ValueError("Missing 'ca_cert' in secrets.toml – please embed the full PEM certificate content")
        
        connect_args = {
            "ssl_ca": ca_content,           # Pass as string (mysql-connector-python accepts this)
            "connect_timeout": 10,
        }
        
        db_url = (
            f"mysql+mysqlconnector://"
            f"{secrets['username']}:{secrets['password']}"
            f"@{secrets['host']}:{secrets['port']}/"
            f"{secrets['database']}"
            "?charset=utf8mb4"
        )
        
        engine = create_engine(db_url, connect_args=connect_args)
        
        # Quick test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
    
    except Exception as e:
        st.error(f"Failed to create database connection: {str(e)}")
        st.stop()


# ────────────────────────────────────────────────
# Public API endpoint: ?api=get_pins → returns JSON
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
            # Convert to string (clean output, consistent with old PHP)
            row = {k: str(v) if v is not None else None for k, v in row.items()}
            st.json(row)
        else:
            st.json({"error": "No records found in pins table"})
            
    except Exception as e:
        st.json({"error": f"Server error: {str(e)}"})
    
    st.stop()  # Prevent normal app UI from rendering


# ────────────────────────────────────────────────
# Normal Streamlit app (main UI)
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Medical4 App",
    page_icon="🏥",
    layout="wide"
)

# Sidebar navigation
st.sidebar.title("Medical4 App")
st.sidebar.markdown("Welcome, Ravi!")
page = st.sidebar.radio("Go to", ["Home", "Latest Pin Record", "About"])

if page == "Home":
    st.title("🏥 Welcome to Medical4 App")
    st.markdown("""
    This is your medical data dashboard powered by TiDB Cloud + Streamlit.
    
    - View the latest pin record
    - API endpoint: `?api=get_pins`
    - More features coming soon (patient forms, charts, login, etc.)
    """)
    
    with st.expander("Debug & Status", expanded=False):
        st.write("Streamlit version:", st.__version__)
        if "tidb" in st.secrets:
            st.success("TiDB secrets section found ✓")
        else:
            st.warning("TiDB secrets section not found in secrets.toml")
        
        try:
            engine = get_db_connection()
            st.success("Database connection successful ✓")
        except Exception as e:
            st.error(f"Connection test failed: {str(e)}")


elif page == "Latest Pin Record":
    st.title("Latest Pin Record")
    
    if st.button("Refresh Latest Record", type="primary"):
        with st.spinner("Fetching from TiDB..."):
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
                    st.success("Record loaded successfully!")
                    st.dataframe(df, use_container_width=True)
                    
                    # Show as nice key-value cards
                    st.subheader("Details")
                    cols = st.columns(3)
                    row = df.iloc[0]
                    for i, col_name in enumerate(["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]):
                        with cols[i % 3]:
                            st.metric(col_name, row[col_name])
                else:
                    st.info("No records found in the 'pins' table.")
                    
            except Exception as e:
                st.error(f"Database error: {str(e)}")


elif page == "About":
    st.title("About Medical4 App")
    st.markdown("""
    ### Purpose
    Medical4 App is a simple dashboard to view and manage medical-related pin data stored in TiDB Cloud.
    
    ### Features (current)
    - Public JSON API (`?api=get_pins`)
    - Display latest record
    - Secure connection using embedded SSL certificate
    
    ### Planned
    - User login / authentication
    - Add new records via form
    - Charts & analytics
    - Export to CSV/PDF
    
    Contact: Ravi (Ludhiana)
    """)


# Footer
st.markdown("---")
st.caption("© 2026 Medical4 App | Powered by Streamlit + TiDB Cloud")
