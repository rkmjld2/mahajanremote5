import streamlit as st
import requests
import json
import time
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("🌍 ESP8266 TiDB REAL CONTROL")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# REAL TiDB Cloud Connection (NO PyMySQL needed)
TIDB_URL = "https://gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/medical4_app"

@st.cache_data(ttl=5)
def get_tidb_pins():
    """Read LATEST pins from TiDB + check ESP activity"""
    try:
        # Direct HTTP to TiDB (works in Streamlit Cloud)
        response = requests.get(
            f"{TIDB_URL}/_read",
            params={
                "user": "ax6KHc1BNkyuaor.root",
                "pass": "EP8isIWoEOQk7DSr",
                "table": "esp_pins",
                "action": "latest"
            },
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            pins = data.get("pins", {p: 0 for p in PINS})
            last_update = data.get("updated_at", "")
            # Check if ESP updated in last 30 seconds
            if last_update:
                last_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                esp_alive = (datetime.now(last_time.tzinfo) - last_time) < timedelta(seconds=30)
                return pins, esp_alive, last_update
        return {p: 0 for p in PINS}, False, "Never"
    except:
        return {p: 0 for p in PINS}, False, "Error"

def write_pins_to_tidb(pins):
    """WRITE pins to TiDB table"""
    try:
        response = requests.post(
            f"{TIDB_URL}/_write",
            json={
                "user": "ax6KHc1BNkyuaor.root",
                "pass": "EP8isIWoEOQk7DSr",
                "table": "esp_pins",
                "pins": pins,
                "source": "web"
            },
            timeout=5
        )
        if response.status_code in [200, 201]:
            return True
        return False
    except:
        return False

# MAIN LOGIC
pins, esp_alive, last_update = get_tidb_pins()

# BIG ESP STATUS
st.markdown("### 📡 ESP8266 STATUS")
col1, col2, col3 = st.columns(3)
col1.metric("Status", "🟢 ONLINE" if esp_alive else "🔴 OFFLINE")
col2.metric("IP", "192.168.1.3")
col3.metric("Last Sync", last_update)

st.markdown("---")

# PIN DISPLAY
st.subheader("📊 CURRENT PINS (from TiDB)")
cols = st.columns(3)
for i, pin in enumerate(PINS):
    state = pins.get(pin, 0)
    cols[i%3].metric(pin, f"🟢 ON" if state else "🔴 OFF")

# CONTROLS - DISABLED WHEN OFFLINE
st.subheader("🔧 PIN CONTROL")
if esp_alive:
    st.success("✅ ESP ONLINE - Controls ACTIVE!")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            state = pins.get(pin, 0)
            new_state = 1 - state  # Toggle
            if st.button(f"{pin}: {'🟢 ON' if new_state else '🔴 OFF'}", key=f"pin_{pin}"):
                pins[pin] = new_state
                if write_pins_to_tidb(pins):
                    st.success(f"✅ {pin} → {'ON' if new_state else 'OFF'} sent to TiDB!")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ TiDB write failed!")
else:
    st.error("🔴 ESP OFFLINE - ALL CONTROLS DISABLED")
    cols = st.columns(3)
    for i, pin in enumerate(PINS):
        with cols[i%3]:
            st.button(f"{pin}: ❌ OFFLINE", disabled=True)

# QUICK ACTIONS
st.subheader("⚡ QUICK ACTIONS")
col1, col2, col3 = st.columns(3)
if esp_alive:
    if col1.button("🌟 ALL ON", type="primary"):
        all_on = {p: 1 for p in PINS}
        write_pins_to_tidb(all_on)
        st.rerun()
    if col2.button("💤 ALL OFF"):
        all_off = {p: 0 for p in PINS}
        write_pins_to_tidb(all_off)
        st.rerun()
    if col3.button("🔄 REFRESH"):
        st.cache_data.clear()
        st.rerun()
else:
    col1.button("🌟 ALL ON", disabled=True)
    col2.button("💤 ALL OFF", disabled=True)
    col3.button("🔄 CHECK ESP", on_click=lambda: st.rerun())

st.markdown("---")
st.info("""
**🌍 HOW IT WORKS:**
1. Web → Click button → WRITES to TiDB `esp_pins` table
2. ESP → Polls TiDB every 10s → Reads pins → Applies to hardware
3. ESP → Writes status back → Web shows real state
4. ESP OFF = No TiDB writes >30s → Web shows OFFLINE

**TiDB Table (run once):**
```sql
CREATE TABLE esp_pins (
  id INT AUTO_INCREMENT PRIMARY KEY,
  D0 TINYINT, D1 TINYINT, D2 TINYINT, D3 TINYINT, 
  D4 TINYINT, D5 TINYINT, D6 TINYINT, D7 TINYINT, D8 TINYINT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  source VARCHAR(20)
);
