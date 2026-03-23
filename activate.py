import secrets
from flask import request, jsonify
import pymysql
from database import connect_db

def register_activate(app):
    @app.route("/activate", methods=["POST"])
    def activate():

        data = request.get_json()

        device_id = data.get("device_id")
        key = data.get("key")

        MASTER_KEY = "HEN-2026-PRO"

        if key != MASTER_KEY:
            return jsonify({"status":"invalid_key"})

        conn = connect_db()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute(
            "SELECT * FROM device WHERE device_id=%s",
            (device_id,)
        )

        device = cur.fetchone()

        if not device:
            return jsonify({"error":"device not found"})

        token = secrets.token_hex(32)

        cur.execute("""
            UPDATE device
            SET activated=1,
                token=%s,
                expire_date=NULL
            WHERE device_id=%s
        """,(token,device_id))

        conn.commit()

        conn.close()

        return jsonify({
            "status":"activated",
            "token":token
        })