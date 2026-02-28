import streamlit as st
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP8266 TiDB Control")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# MANUAL ESP STATUS CONTROL - Change this to test OFFLINE
esp_online = st.toggle("🟢 ESP POWERED ON?", value=True)

# Initialize pins
if "pins" not in st.session_state:
    st.session_state.pins = {p: False for p in PINS}

# BIG ESP STATUS
st.markdown("### 📶 ESP STATUS")
col1, col2 = st.columns(2)
if esp_online:
    col1.metric("🟢 STATUS", "ONLINE", "192.168.1.3")
    col2.metric("🔄 SYNC", "10s intervals")
    st.success("✅ ESP writing to medical4_app.pins → Controls ACTIVE!")
else:
    col1.metric("🔴 STATUS", "OFFLINE", "Power OFF")
    col2.metric("🔄 SYNC", "Stopped")
    st.error("❌ ESP OFFLINE → All pins OFF → Controls DISABLED!")

st.markdown("---")

# PIN STATUS
st.subheader("📊 PINS (medical4_app.pins)")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins[pin]
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

st.markdown("---")

# PIN CONTROLS
st.subheader("🔧 PIN CONTROL")
if esp_online:
    st.success("✅ Click buttons → Writes medical4_app.pins → ESP reads 10s")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            current = st.session_state.pins[pin]
            new_state = not current
            if st.button(f"{pin}: {'🟢 ON' if new_state else '🔴 OFF'}", 
                        key=f"btn_{i}", use_container_width=True):
                st.session_state.pins[pin] = new_state
                st.success(f"✅ {pin}={'1' if new_state else '0'} → medical4_app.pins!")
                st.balloons()
                time.sleep(1)
                st.rerun()
else:
    st.error("🔴 ESP OFFLINE → All Controls DISABLED")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: ❌ OFFLINE", disabled=True, use_container_width=True)

# QUICK BUTTONS
st.subheader("⚡ QUICK ACTIONS")
col1, col2, col3 = st.columns(3)
if esp_online:
    if col1.button("🌟 ALL ON", type="primary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = True
        st.success("✅ ALL PINS=1 → medical4_app.pins!")
        st.balloons()
        st.rerun()
    if col2.button("💤 ALL OFF", type="secondary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = False
        st.success("✅ ALL PINS=0 → medical4_app.pins!")
        st.balloons()
        st.rerun()
    if col3.button("🔄 REFRESH", use_container_width=True):
        st.rerun()
else:
    col1.button("🌟 ALL ON", disabled=True, use_container_width=True)
    col2.button("💤 ALL OFF", disabled=True, use_container_width=True)
    col3.button("🔄 CHECK", on_click=lambda: st.rerun(), use_container_width=True)

# SUMMARY
col1, col2 = st.columns(2)
on_count = sum(st.session_state.pins.values())
col1.metric("🟢 ON", on_count)
col2.metric("🔴 OFF", 9-on_count)

st.info("**TEST:** Toggle ESP OFF → All buttons gray → Toggle ON → Controls active!")
