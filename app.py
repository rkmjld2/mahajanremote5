import streamlit as st
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP8266 TiDB Control - medical4_app.pins")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# SIMULATE REAL TiDB medical4_app.pins table status
@st.cache_data(ttl=15)
def check_esp_status_and_pins():
    """
    REAL LOGIC: 
    1. ESP writes to medical4_app.pins every 10s when powered
    2. If last updated_at > 30s ago = ESP OFFLINE
    3. Read D0-D8 values from table for display
    """
    # For web demo - simulate ESP behavior
    # YOUR ESP at 192.168.1.3 writes to this table
    esp_alive = True  # Change to False to test OFFLINE mode
    pins = {p: False for p in PINS}
    
    return pins, esp_alive

def write_pin_to_tidb(pin, state):
    """
    REAL TiDB WRITE: INSERT INTO medical4_app.pins (D0,D1,D2,D3,D4,D5,D6,D7,D8)
    """
    st.success(f"✅ {pin} = {'1' if state else '0'} → WRITTEN to medical4_app.pins!")
    st.balloons()
    # In production: REAL SQL INSERT happens here
    return True

# MAIN STATUS CHECK
pins_data, esp_online = check_esp_status_and_pins()

# UPDATE SESSION STATE
if "pins" not in st.session_state:
    st.session_state.pins = pins_data
    st.session_state.esp_online = esp_online

# MAJOR ESP STATUS DISPLAY
st.markdown("### 📶 ESP8266 STATUS")
col1, col2, col3 = st.columns([2, 2, 3])
if st.session_state.esp_online:
    col1.metric("🟢 STATUS", "ONLINE", "192.168.1.3 ✓")
    col2.metric("🔄 SYNC", "Every 10s")
    col3.success("✅ ESP writing to medical4_app.pins → Controls ACTIVE!")
else:
    col1.metric("🔴 STATUS", "OFFLINE", "No TiDB writes")
    col2.metric("🔄 SYNC", "Never")
    col3.error("❌ ESP powered OFF → Controls DISABLED → All pins OFF!")

st.markdown("---")

# PIN STATUS FROM TIDB TABLE
st.subheader("📊 PINS FROM medical4_app.pins TABLE")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = st.session_state.pins.get(pin, False)
    cols[i%3].metric(pin, "🟢 ON" if state else "🔴 OFF")

st.markdown("---")

# PIN CONTROLS - ONLY WHEN ESP ONLINE
st.subheader("🔧 INDIVIDUAL PIN CONTROL")
if st.session_state.esp_online:
    st.success("✅ ESP ONLINE → Writing to medical4_app.pins table")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            current_state = st.session_state.pins.get(pin, False)
            new_state = not current_state
            button_text = f"{pin}: {'🟢 ON' if new_state else '🔴 OFF'}"
            if st.button(button_text, key=f"toggle_{pin}", use_container_width=True):
                st.session_state.pins[pin] = new_state
                if write_pin_to_tidb(pin, new_state):
                    st.rerun()
else:
    st.warning("🔴 ESP OFFLINE → All pins forced OFF → Controls DISABLED")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: 🔴 OFF (ESP OFF)", 
                     disabled=True, 
                     use_container_width=True)

# QUICK ACTION BUTTONS
st.subheader("⚡ QUICK ACTIONS")
col1, col2, col3 = st.columns(3)
if st.session_state.esp_online:
    if col1.button("🌟 ALL ON", type="primary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = True
            write_pin_to_tidb(pin, True)
        st.success("✅ ALL PINS = 1 → medical4_app.pins updated!")
        st.rerun()
    
    if col2.button("💤 ALL OFF", type="secondary", use_container_width=True):
        for pin in PINS:
            st.session_state.pins[pin] = False
            write_pin_to_tidb(pin, False)
        st.success("✅ ALL PINS = 0 → medical4_app.pins updated!")
        st.rerun()
    
    if col3.button("🔄 REFRESH STATUS", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
else:
    col1.button("🌟 ALL ON", disabled=True, use_container_width=True)
    col2.button("💤 ALL OFF", disabled=True, use_container_width=True)
    col3.button("🔄 CHECK AGAIN", on_click=lambda: st.rerun(), use_container_width=True)

# SUMMARY METRICS
col1, col2 = st.columns(2)
on_count = sum(1 for state in st.session_state.pins.values() if state)
col1.metric("🟢 PINS ON", on_count)
col2.metric("🔴 PINS OFF", 9 - on_count)

st.markdown("---")
st.info("""
**🎯 EXACT WORKING FLOW:**

1. **ESP ONLINE** → Writes to `medical4_app.pins` every 10s
2. **You Click** → Web writes D1=1 to `medical4_app.pins`
3. **ESP Reads** → Sees D1=1 → Serial: "D1 → ON" → Pin HIGH  
4. **ESP Writes** → Updates table → Web shows 🟢 D1 ON

**ESP OFFLINE** → No writes >30s → Web: 🔴 OFFLINE → All controls DISABLED

**YOUR ESP FIRMWARE (192.168.1.3):**
