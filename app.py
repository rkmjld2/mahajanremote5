from flask import Flask, jsonify
import mysql.connector
import os

app = Flask(__name__)

# Read from env vars (set in Render dashboard)
db_config = {
    "host": os.getenv("TIDB_HOST"),
    "port": int(os.getenv("TIDB_PORT", 4000)),
    "user": os.getenv("TIDB_USER"),
    "password": os.getenv("TIDB_PASSWORD"),
    "database": os.getenv("TIDB_DATABASE"),
    "ssl_ca": os.getenv("TIDB_SSL_CA"),
    "ssl_verify_cert": True,
}

@app.route('/get_pins', methods=['GET'])
def get_pins():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT D0,D1,D2,D3,D4,D5,D6,D7,D8 FROM pins LIMIT 1")
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return jsonify(row or {"D0":0,"D1":0,"D2":0,"D3":0,"D4":0,"D5":0,"D6":0,"D7":0,"D8":0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))
