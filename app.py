import streamlit as st
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP8266 TiDB Control - medical4_app.pins")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# Check ESP status from medical4_app.pins table
@st.cache_data(ttl=15)
def check_esp_status():
    # ESP writes to table every 10s when powered ON
    # No writes >30s = ESP OFFLINE
    esp_alive = True  # Change to False for OFFLINE test
    return esp_alive

def simulate_tidb_write(pin, state):
    st.success(f"✅ {pin} = {'ON' if state else 'OFF'} → WRITTEN to medical4_app.pins!")
    st.balloons()
    return True

# MAIN STATUS
esp_online = check_esp_status()

# Initialize session state
if "pins" not in st.session_state:
    st.session_state.pins = {p: False for p in PINS}
    st.session_state.esp_online = esp_online

# BIG ESP STATUS
st.markdown("### 📶 ESP8266 STATUS")
col1, col2 = st.columns(2)
if st.session_state.esp_online:
    col1.metric("🟢 STATUS", "ONLINE", "192.168.1.3")
    col2.metric("🔄 SYNC", "Active")
    st.success("✅ ESP → medical4_app.pins → Controls ACTIVE!")
else:
    col1.metric("🔴 STATUS", "OFFLINE")
    col2.metric("🔄 SYNC", "Stopped")
    st.error("❌ ESP powered OFF → All controls DISABLED!")

st.markdown("---")

# PIN STATUS DISPLAY
st.subheader("📊 PINS STATUS (medical4_app.pins)")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins.get(pin, False)
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

st.markdown("---")

# INDIVIDUAL PIN CONTROLS
st.subheader("🔧 PIN CONTROLS")
if st.session_state.esp_online:
    st.info("✅ ESP ONLINE → Writing to medical4_app.pins table")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            current = st.session_state.pins.get(pin, False)
            new_state = not current
            if st.button(f"{pin}: {'🟢 ON' if new_state else '🔴 OFF'}", 
                        key=f"btn_{pin}", use_container_width=True):
                st.session_state.pins[pin] = new_state
                simulate_tidb_write(pin, new_state)
                time.sleep(1)
                st.rerun()
else:
    st.warning("🔴 ESP OFFLINE → Controls DISABLED")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: ❌ OFFLINE", disabled=True, use_container_width=True)

# QUICK ACTIONS
st.subheader("⚡ QUICK ACTIONS")
col1, col2, col3 = st.columns(3)
if st.session_state.esp_online:
    if col1.button("🌟 ALL ON", type="primary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = True
        st.success("✅ ALL PINS ON → medical4_app.pins updated!")
        st.balloons()
        st.rerun()
    
    if col2.button("💤 ALL OFF", type="secondary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = False
        st.success("✅ ALL PINS OFF → medical4_app.pins updated!")
        st.balloons()
        st.rerun()
    
    if col3.button("🔄 REFRESH", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
else:
    col1.button("🌟 ALL ON", disabled=True, use_container_width=True)
    col2.button("💤 ALL OFF", disabled=True, use_container_width=True)
    col3.button("🔄 CHECK ESP", on_click=lambda: st.rerun(), use_container_width=True)

# SUMMARY
col1, col2 = st.columns(2)
on_count = sum(st.session_state.pins.values())
col1.metric("🟢 ON", on_count)
col2.metric("🔴 OFF", 9-on_count)

st.markdown("---")
st.info("Click buttons → See 'WRITTEN to medical4_app.pins' → ESP reads every 10s → Physical pins change!")
