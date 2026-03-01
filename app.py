from flask import Flask, jsonify
import mysql.connector
import os
import tempfile

app = Flask(__name__)

# === YOUR TiDB CREDENTIALS (copy from Streamlit secrets) ===
HOST = "gateway01.ap-southeast-1.prod.aws.tidbcloud.com"
PORT = 4000
USER = "ax6KHc1BNkyuaor.root"
PASSWORD = "EP8isIWoEOQk7DSr"
DATABASE = "medical4_app"

SSL_CA = """-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
ZXQgU2VjdXyaXR5IFJlc2VhcmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
... (paste your FULL certificate here exactly as in Streamlit secrets)
-----END CERTIFICATE-----"""

def get_db_connection():
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pem') as f:
        f.write(SSL_CA.encode('utf-8'))
        ca_path = f.name
    conn = mysql.connector.connect(
        host=HOST, port=PORT, user=USER, password=PASSWORD, database=DATABASE,
        ssl_ca=ca_path, ssl_verify_cert=True, ssl_verify_identity=False,
        use_pure=True
    )
    return conn, ca_path

@app.route('/get_pins')
def get_pins():
    ca_path = None
    try:
        conn, ca_path = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        result = row or {"D0":0,"D1":0,"D2":0,"D3":0,"D4":0,"D5":0,"D6":0,"D7":0,"D8":0}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if ca_path and os.path.exists(ca_path):
            os.unlink(ca_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
