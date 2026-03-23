import pytz
from flask import request, jsonify
import pymysql
from datetime import datetime, timedelta
from database import connect_db

def register_check_device(app):
    @app.route("/time")
    def time():
        return {
            "server_time": str(datetime.now()),
            "server_date": str(datetime.today().date())
        }
    @app.route("/check-device", methods=["POST"])
    def check_device():

        data = request.get_json()
        device_id = data.get("device_id")

        conn = connect_db()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        cur.execute(
            "SELECT * FROM device WHERE device_id=%s",
            (device_id,)
        )

        device = cur.fetchone()

        # today = datetime.today().date() trên rander là lấy bn dươi gio vn
        # tz = pytz.timezone("Asia/Ho_Chi_Minh")
        # today = datetime.now(tz).date()
        from datetime import datetime, timezone, timedelta

        today = (datetime.now(timezone.utc) + timedelta(hours=7)).date()

        # 1️⃣ chưa tồn tại → tạo trial
        if not device:
            expire = today + timedelta(days=7)  # 1 tuần

            cur.execute("""
                INSERT INTO device (device_id, first_install, expire_date, activated)
                VALUES (%s,%s,%s,%s)
            """, (device_id, today, expire, False))

            conn.commit()
            conn.close()

            return jsonify({
                "status": "trial",
                "expire_date": expire.strftime("%Y-%m-%d"),
                "server_date": today.strftime("%Y-%m-%d"),  # thêm dòng này
                "token": None
            })
        # 2️⃣ đã kích hoạt
        if device["activated"]:
            conn.close()

            return jsonify({
                "status":"activated",
                "expire_date":device["expire_date"].strftime("%Y-%m-%d"),
                "token":device["token"]
            })

        # 3️⃣ hết hạn tới ngày này là hết
        expire_date = device["expire_date"]

        # nếu là datetime thì chuyển sang date
        if isinstance(expire_date, datetime):
            expire_date = expire_date.date()

        if expire_date and today >= expire_date:


            conn.close()

            return jsonify({
                "status":"expired",
                "expire_date":device["expire_date"].strftime("%Y-%m-%d"),
                "server_date": today.strftime("%Y-%m-%d")
            })

        # 4️⃣ trial
        conn.close()

        return jsonify({
            "status":"trial",
            "expire_date":device["expire_date"].strftime("%Y-%m-%d"),
            "token":None
        })