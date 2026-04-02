from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 4000)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        autocommit=True
    )

# ---------- API KEY ----------
API_KEY = os.environ.get("SECRET_KEY")


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html")


# ---------- RECEIVE DATA FROM ESP ----------
@app.route("/api/data")
def receive_data():
    try:
        key = request.args.get("key", "").strip()

        if key != (API_KEY or "").strip():
            return "unauthorized", 403

        s1 = request.args.get("s1")
        s2 = request.args.get("s2")
        s3 = request.args.get("s3")

        if not s1 or not s2 or not s3:
            return "missing", 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp) VALUES (%s,%s,%s,NOW())",
            (s1, s2, s3)
        )

        cursor.close()
        conn.close()

        # 🔥 VERY FAST RESPONSE (NO TIMEOUT)
        return "OK"

    except Exception as e:
        print("INSERT ERROR:", e)
        return "ERR"


# ---------- GET DATA ----------
@app.route("/api/getdata")
def get_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            ORDER BY id DESC
            LIMIT 100
        """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert to IST
        for row in data:
            if row["timestamp"]:
                row["timestamp"] = (row["timestamp"] + timedelta(hours=5, minutes=30)).strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(data)

    except Exception as e:
        print("FETCH ERROR:", e)
        return jsonify([])


# ---------- STATUS ----------
@app.route("/api/status")
def status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT timestamp FROM sensor_db ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({"status": "disconnected"})

        last_time = row["timestamp"]
        now = datetime.utcnow()

        diff = (now - last_time).total_seconds()

        if diff < 15:
            return jsonify({"status": "connected"})
        else:
            return jsonify({"status": "disconnected"})

    except:
        return jsonify({"status": "disconnected"})


# ---------- SEARCH BY DATE ----------
@app.route("/api/search/date")
def search_date():
    try:
        start = request.args.get("start")
        end = request.args.get("end")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, sensor1, sensor2, sensor3, timestamp
            FROM sensor_db
            WHERE timestamp BETWEEN %s AND %s
            ORDER BY id DESC
        """, (start, end))

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print("DATE ERROR:", e)
        return jsonify([])


# ---------- CUSTOM QUERY ----------
@app.route("/api/search/query")
def custom_query():
    try:
        q = request.args.get("q", "").strip().lower()

        if not q:
            return jsonify({"error": "empty query"})

        if any(x in q for x in ["drop", "truncate", "alter", "create"]):
            return jsonify({"error": "blocked query"})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(q)

        if q.startswith("select"):
            data = cursor.fetchall()
            return jsonify(data)
        else:
            conn.commit()
            return jsonify({"status": "success", "rows": cursor.rowcount})

    except Exception as e:
        print("QUERY ERROR:", e)
        return jsonify({"error": str(e)})


# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True)
