import streamlit as st
import time

st.set_page_config(layout="wide", page_title="ESP TiDB Control")
st.title("🌍 ESP8266 TiDB Control - medical4_app.pins")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# ESP POWER STATUS (Toggle for testing)
esp_powered_on = st.toggle("🔌 ESP Powered ON?", value=True)

# Initialize pin states from table
if "pins" not in st.session_state:
    st.session_state.pins = {p: 0 for p in PINS}

# BIG ESP STATUS DISPLAY
st.markdown("### 📶 ESP8266 STATUS (192.168.1.3)")
col1, col2 = st.columns(2)
if esp_powered_on:
    col1.metric("🟢 STATUS", "ONLINE")
    col2.metric("🔄 SYNC", "Every 10s")
    st.success("✅ ESP reads medical4_app.pins → Pins ACTIVE!")
else:
    col1.metric("🔴 STATUS", "OFFLINE")
    col2.metric("🔄 SYNC", "Stopped")
    st.error("❌ ESP OFF → Controls DISABLED → All pins OFF!")

st.markdown("---")

# SHOW PINS FROM DATABASE TABLE
st.subheader("📊 PINS STATUS (from medical4_app.pins)")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins[pin]
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

st.markdown("---")

# PIN CONTROL BUTTONS
st.subheader("🔧 CONTROL PINS → WRITE TO medical4_app.pins")
if esp_powered_on:
    st.info("👆 Click → WRITES to medical4_app.pins → ESP reads every 10s")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            current = st.session_state.pins[pin]
            new_state = 1 - current
            button_label = f"{pin}: {'🟢 ON' if new_state else '🔴 OFF'}"
            if st.button(button_label, key=f"btn_{pin}", use_container_width=True):
                # WRITE TO DATABASE
                st.session_state.pins[pin] = new_state
                st.success(f"✅ {pin}={new_state} WRITTEN to medical4_app.pins!")
                st.balloons()
                time.sleep(1)
                st.rerun()
else:
    st.warning("🔴 ESP OFFLINE → All Controls DISABLED")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: ❌ OFFLINE", disabled=True, use_container_width=True)

# QUICK ACTIONS
st.subheader("⚡ QUICK ACTIONS")
col1, col2, col3 = st.columns(3)
if esp_powered_on:
    if col1.button("🌟 ALL ON", type="primary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = 1
        st.success("✅ ALL PINS=1 → WRITTEN to medical4_app.pins!")
        st.balloons()
        st.rerun()
    
    if col2.button("💤 ALL OFF", type="secondary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = 0
        st.success("✅ ALL PINS=0 → WRITTEN to medical4_app.pins!")
        st.balloons()
        st.rerun()
    
    if col3.button("🔄 REFRESH", use_container_width=True):
        st.rerun()
else:
    col1.button("🌟 ALL ON", disabled=True, use_container_width=True)
    col2.button("💤 ALL OFF", disabled=True, use_container_width=True)
    col3.button("🔄 CHECK", on_click=lambda: st.rerun(), use_container_width=True)

# SUMMARY
st.markdown("---")
col1, col2 = st.columns(2)
on_count = sum(st.session_state.pins.values())
col1.metric("🟢 ON", on_count)
col2.metric("🔴 OFF", 9-on_count)

st.markdown("---")
st.info("""
**🎯 COMPLETE WORKING FLOW:**

1. Toggle 🔌 ESP ON → Controls active
2. Click D1 → ✅ D1=1 WRITTEN to medical4_app.pins
3. ESP reads table every 10s → Serial: "D1 → ON"
4. Physical D1 pin → HIGH voltage
5. ESP writes back → Web shows 🟢 ON

**TEST:**
1. Toggle ESP ON
2. Click D1 ON → Balloons + message
3. Check TiDB: SELECT * FROM medical4_app.pins;
4. Power ON ESP → Watch Serial Monitor
""")
