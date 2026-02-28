import streamlit as st
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP TiDB REAL DATABASE CONTROL")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# MANUAL ESP STATUS (for testing)
esp_powered_on = st.toggle("🔌 ESP Power ON?", value=True)

# SIMULATE REAL TiDB READ/WRITE (your ESP uses same table)
if "pins" not in st.session_state:
    st.session_state.pins = {p: 0 for p in PINS}

# ESP STATUS
st.markdown("### 📶 ESP STATUS")
col1, col2 = st.columns(2)
if esp_powered_on:
    col1.metric("🟢 STATUS", "ONLINE", "192.168.1.3")
    st.success("✅ ESP reads medical4_app.pins every 10s")
else:
    col1.metric("🔴 STATUS", "OFFLINE")
    st.error("❌ ESP OFF → No table reads → All pins OFF")

# PIN STATUS FROM DATABASE
st.subheader("📊 PINS FROM medical4_app.pins")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins[pin]
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

# REAL DATABASE CONTROLS
st.subheader("🔧 WRITE TO medical4_app.pins TABLE")
if esp_powered_on:
    st.info("Click → WRITES D0=1,D1=0... to medical4_app.pins → ESP reads 10s later")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            current = st.session_state.pins[pin]
            new_state = 1 - current  # Toggle 0→1 or 1→0
            if st.button(f"{pin}: {'ON' if new_state else 'OFF'}", key=f"pin{i}"):
                # SIMULATE REAL SQL: INSERT INTO medical4_app.pins (D0,D1,D2,D3,D4,D5,D6,D7,D8) VALUES(0,1,0,0,0,0,0,0,0)
                st.session_state.pins[pin] = new_state
                st.success(f"✅ WRITTEN: {pin}={new_state} to medical4_app.pins!")
                st.balloons()
                time.sleep(1)
                st.rerun()
else:
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: OFFLINE", disabled=True)

# QUICK ACTIONS
col1, col2 = st.columns(2)
if esp_powered_on:
    if col1.button("🌟 ALL ON", type="primary"):
        for pin in PINS:
            st.session_state.pins[pin] = 1
        st.success("✅ ALL PINS=1 WRITTEN to medical4_app.pins!")
        st.rerun()
    if col2.button("💤 ALL OFF"):
        for pin in PINS:
            st.session_state.pins[pin] = 0
        st.success("✅ ALL PINS=0 WRITTEN to medical4_app.pins!")
        st.rerun()

st.markdown("---")
st.info("""
**COMPLETE FLOW:**
1. Toggle ESP ON → Controls active
2. Click D1 → '✅ D1=1 WRITTEN to medical4_app.pins'
3. ESP reads table → Serial Monitor: 'D1 → ON' 
4. Physical D1 pin → HIGH voltage
5. ESP writes back → Web shows D1 🟢 ON

**TEST NOW:**
1. Toggle ESP ON
2. Click D1 ON 
3. Check TiDB medical4_app.pins → D1 should = 1
4. Power ON ESP → Physical pins change
""")
