import streamlit as st
import requests
import json
import time

st.set_page_config(layout="wide")
st.title("🌍 ESP8266 TiDB Global Control")

PINS = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

# HTTP API to TiDB (works everywhere!)
@st.cache_data(ttl=5)
def get_pins():
    try:
        response = requests.post(
            "https://gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/medical4_app/esp_pins",
            json={"user": "ax6KHc1BNkyuaor.root", "pass": "EP8isIWoEOQk7DSr", "action": "read"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get("pins", {p: False for p in PINS})
    except:
        pass
    return {p: False for p in PINS}

def set_pins(pins):
    try:
        requests.post(
            "https://gateway01.ap-southeast-1.prod.aws.tidbcloud.com:4000/medical4_app/esp_pins",
            json={
                "user": "ax6KHc1BN
