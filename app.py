from flask import Flask, request, jsonify, render_template
import mysql.connector
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        port=int(os.environ.get("DB_PORT", 4000)),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        autocommit=True,
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
            return jsonify({"status": "unauthorized"}), 403

        s1 = request.args.get("s1")
        s2 = request.args.get("s2")
        s3 = request.args.get("s3")

        if not s1 or not s2 or not s3:
            return jsonify({"status": "missing data"})

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO sensor_db (sensor1, sensor2, sensor3, timestamp)
        VALUES (%s, %s, %s, NOW())
        """

        cursor.execute(query, (s1, s2, s3))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        print("INSERT ERROR:", e)
        return jsonify({"status": "error", "message": str(e)})


# ---------- GET LATEST DATA ----------
@app.route("/api/getdata")
def get_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        ORDER BY id DESC
        LIMIT 100
        """

        cursor.execute(query)
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert UTC → IST
        for row in data:
            if row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(data)

    except Exception as e:
        print("FETCH ERROR:", e)
        return jsonify([])


# ---------- SEARCH BY DATE ----------
@app.route("/api/search/date")
def search_by_date():
    try:
        start = request.args.get("start")
        end = request.args.get("end")

        if not start or not end:
            return jsonify([])

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
        SELECT id, sensor1, sensor2, sensor3, timestamp
        FROM sensor_db
        WHERE timestamp BETWEEN %s AND %s
        ORDER BY id DESC
        """

        cursor.execute(query, (start, end))
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        # Convert UTC → IST
        for row in data:
            if row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(data)

    except Exception as e:
        print("DATE SEARCH ERROR:", e)
        return jsonify([])


# ---------- CUSTOM QUERY ----------
@app.route("/api/search/query")
def search_by_query():
    try:
        q = request.args.get("q", "").strip()

        if not q:
            return jsonify({"error": "query is empty"})

        lower = q.lower()

        # Block dangerous queries
        if any(k in lower for k in ("drop ", "truncate ", "alter ", "create ")):
            return jsonify({"error": "dangerous query blocked"})

        # Allow only safe operations
        if not (
            lower.startswith("select") or
            lower.startswith("delete") or
            lower.startswith("update")
        ):
            return jsonify({"error": "only SELECT/DELETE/UPDATE allowed"})

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(q)

        if lower.startswith("select"):
            rows = cursor.fetchall()
        else:
            conn.commit()
            return jsonify({
                "status": "success",
                "rows_affected": cursor.rowcount
            })

        cursor.close()
        conn.close()

        # Format timestamp
        for row in rows:
            if "timestamp" in row and row["timestamp"]:
                dt = row["timestamp"].replace(tzinfo=timezone.utc)
                ist = dt + timedelta(hours=5, minutes=30)
                row["timestamp"] = ist.strftime("%d/%m/%Y %H:%M:%S")

        return jsonify(rows)

    except Exception as e:
        print("CUSTOM QUERY ERROR:", e)
        return jsonify({"error": str(e)})
#............................
@app.route("/api/status")
def status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT timestamp FROM sensor_db
            ORDER BY id DESC LIMIT 1
        """)
        row = cursor.fetchone()

        cursor.close()
        conn.close()

        if not row:
            return jsonify({"status": "disconnected"})

        last = row["timestamp"]
        now = datetime.utcnow()

        diff = (now - last).total_seconds()

        if diff < 15:
            return jsonify({"status": "connected"})
        else:
            return jsonify({"status": "disconnected"})

    except:
        return jsonify({"status": "disconnected"})

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(debug=True)
