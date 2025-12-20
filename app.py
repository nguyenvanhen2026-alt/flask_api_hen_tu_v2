from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app)  # Cho phép CORS nếu Android gọi API
import pymysql.cursors

def connect_db():
    return pymysql.connect(
        host=os.environ.get("AIVEN_HOST"),
        user=os.environ.get("AIVEN_USER"),
        password=os.environ.get("AIVEN_PASS"),
        database=os.environ.get("AIVEN_DB"),
        port=int(os.environ.get("AIVEN_PORT")),
        ssl={"ca": os.path.join(os.getcwd(), "ca.pem")}
    )

@app.route("/")
def home():
    return "API Flask Railway OK!"

@app.route("/get_data", methods=["GET"])
def getall():
    try:
        conn = connect_db()
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("""
            SELECT
                id,
                local_id,
                DATE_FORMAT(ngay, '%Y-%m-%d') AS ngay,
                sothutu,
                tenhang,
                soluong,
                page,
                pageName,
                TIME_FORMAT(tgian, '%H:%i:%s') AS tgian
            FROM dulieu
        """)

        rows = cur.fetchall()
        conn.close()
        return jsonify({"success": True, "data": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
#insert 1 item
@app.route("/add_data", methods=["POST"])
def add():
    try:
        data = request.get_json()
        id=data.get("id")
        ngay = data.get("ngay")
        stt = data.get("stt")
        tenhang = data.get("tenhang")
        soluong = data.get("soluong")
        page = data.get("page")
        pageName = data.get("pageName")

        conn = connect_db()
        cur = conn.cursor()
        sql = "INSERT INTO dulieu (local_id,ngay, sothutu, tenhang, soluong, page, pageName) VALUES (%s,%s, %s, %s, %s, %s, %s)"
        cur.execute(sql, (id,ngay, stt, tenhang, soluong, page, pageName))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
# --- insert nhiều dòng--

@app.route("/upload_bulk", methods=["POST"])
def upload_bulk():
    try:
        data = request.get_json()
        items = data.get("records", [])  # lấy đúng list Server nhận "records" (an toàn, tương thích với Android):
        if not items:
            return jsonify({"success": False, "error": "No records found"})
            # chỉ lưu giờ

        conn = connect_db()
        cur = conn.cursor()
        # sql = "INSERT INTO dulieu (id,ngay, stt, tenhang, soluong, page, pageName,tgian) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
        sql = """
        INSERT INTO dulieu (local_id, ngay, sothutu, tenhang, soluong, page, pageName, tgian)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        for item in items:
            # -------- XỬ LÝ NGÀY ----------
            ngay_str = item.get("ngay")
            try:
                # nếu Android gửi kiểu "Sat, 03 Dec 2025 ..."
                ngay = datetime.strptime(ngay_str[:16], "%a, %d %b %Y").date()
            except:
                # nếu đã là YYYY-MM-DD
                ngay = ngay_str

            # -------- GIỜ SERVER ----------
            VN = timezone(timedelta(hours=7))
            tgian = datetime.now(VN).strftime("%H:%M:%S")

            cur.execute(sql, (
                    item.get("local_id"),
                    ngay,
                    item.get("stt"),
                    item.get("tenhang"),
                    item.get("soluong"),
                    item.get("page"),
                    item.get("pageName"),
                    tgian
                ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "inserted": len(items)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    #lấy tg lớn nhât trong ngày vvaftheo trang
@app.route("/get_last_time", methods=["GET"])
def get_last_time():
    ngay = request.args.get("ngay")
    page = request.args.get("page", type=int)

    if not ngay or page is None:
        return jsonify({"success": False, "error": "missing ngay or page"}), 400

    try:
        conn = connect_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        cursor.execute("""
            SELECT MAX(tgian) AS last_time
            FROM dulieu
            WHERE ngay = %s AND page = %s
        """, (ngay, page))

        row = cursor.fetchone()

        cursor.close()
        conn.close()

        # ⭐ FIX: convert timedelta/time → string
        last_time = str(row["last_time"]) if row and row["last_time"] else None
        return jsonify({"success": True, "last_time": last_time})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# --- Update tenhang theo id ---
@app.route("/update_tenhang/<int:id>", methods=["POST"])
def update_tenhang(id):
    try:
        data = request.get_json()
        new_ten = data.get("tenhang")
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE dulieu SET tenhang=%s WHERE local_id=%s", (new_ten, id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "updated_id": id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- Update soluong theo id ---
@app.route("/update_soluong/<int:id>", methods=["POST"])
def update_soluong(id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON received"}), 400
        new_sl = data.get("soluong")
        conn = connect_db()
        cur = conn.cursor()
        cur.execute("UPDATE dulieu SET soluong=%s WHERE local_id=%s", (new_sl, id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "updated_id": id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# --- Delete theo stt + page + ngay ---
@app.route("/delete_by_page_date", methods=["DELETE"])
def delete_by_page_date():
    try:
        page = request.args.get("page", type=int)
        ngay = request.args.get("ngay", type=str)

        if page is None or not ngay:
            return jsonify({"success": False, "error": "Missing page or ngay parameter"}), 400

        conn = connect_db()
        cur = conn.cursor()

        # MySQL uses %s placeholders
        query = "DELETE FROM dulieu WHERE page = %s AND ngay = %s"
        cur.execute(query, (page, ngay))
        affected = cur.rowcount

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "deleted_rows": affected, "page": page, "ngay": ngay})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/update_name_by_page', methods=['POST'])
def update_name_by_page():
    try:
        data = request.get_json()
        page = data.get("page")
        namePg = data.get("pageName")
        ngay = data.get("ngay")

        if page is None or ngay is None:
            return jsonify({"success": False, "message": "Missing page or ngay"}), 400

        conn = connect_db()  # connect_db phải trả về connection MySQL
        cur = conn.cursor()

        sql = """
            UPDATE dulieu
            SET pageName = %s
            WHERE page = %s AND ngay = %s
        """
        cur.execute(sql, (namePg, page, ngay))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "Updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# --- API insert hoặc update ---
# --- API insert-only --- ok này

@app.route("/insert_aiven", methods=["POST"])
def insert_aiven():
    try:
        data = request.get_json()
        id = data.get("id")
        ngay = data.get("ngay")
        stt = data.get("stt")
        tenhang = data.get("tenhang")
        soluong = data.get("soluong")
        page = data.get("page")
        pageName = data.get("pageName")
        # chỉ lưu giờ
        tgian = datetime.now().strftime("%H:%M:%S")
        conn = connect_db()
        cur = conn.cursor()

        # Chỉ insert mới, id sẽ tự tăng (AI)
        cur.execute("""
            INSERT INTO dulieu (local_id, ngay, sothutu, tenhang, soluong, page, pageName,tgian)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (id, ngay, stt, tenhang, soluong, page, pageName,tgian))

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "action": "inserted"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
#@@@@@@@@@@@@
@app.route("/get_data_by_date", methods=["GET"])
def get_data_by_date():
    ngay_raw = request.args.get("ngay")

    if not ngay_raw:
        return jsonify({"status": "error", "message": "ngay là bắt buộc"}), 400

    # Convert ngày (luôn chạy)
    try:
        ngay = convert_ngay(ngay_raw)
    except Exception as e:
        print("LỖI PARSE NGÀY:", e)
        return jsonify({"status": "error", "message": "Ngày không hợp lệ"}), 400

    conn = connect_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("""
        SELECT local_id, ngay, sothutu, tenhang, soluong, page, pageName
        FROM dulieu_demo.dulieu
        WHERE ngay = %s
    """, (ngay,))
    rows = cursor.fetchall()

    data = []
    for r in rows:
        ngay_value = r["ngay"]
        if not isinstance(ngay_value, str):
            ngay_value = ngay_value.strftime("%Y-%m-%d")

        data.append({
            "id": r["local_id"],
            "ngay": ngay_value,
            "stt": r["sothutu"],
            "tenhang": r["tenhang"],
            "soluong": r["soluong"],
            "page": r["page"],
            "pageName": r["pageName"]
        })

    cursor.close()
    conn.close()

    return jsonify({"success": True, "data": data})


#@@@@@@@@@@@@@@@@@@@@@@ Dùng DATE(2025-12-3) trong MySQL để ép so sánh theo ngày:
@app.route("/get_by_page_date", methods=["GET"])
def get_by_page_date():
    try:
        page = request.args.get("page")
        ngay_raw = request.args.get("ngay")

        if not page or not ngay_raw:
            return jsonify({"status": "error", "message": "page và ngay là bắt buộc"}), 400

        # Convert ngày về yyyy-MM-dd
        ngay = convert_ngay(ngay_raw)

        conn = connect_db()
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        query = """
            SELECT local_id, ngay, sothutu, tenhang, soluong, page, pageName
            FROM dulieu_demo.dulieu
            WHERE page = %s AND DATE(ngay) = %s
        """

        cursor.execute(query, (int(page), ngay))
        rows = cursor.fetchall()

        data = []
        for r in rows:
            ngay_value = r["ngay"]
            if not isinstance(ngay_value, str):
                ngay_value = ngay_value.strftime("%Y-%m-%d")

            data.append({
                "id": r["local_id"],
                "ngay": ngay_value,
                "stt": r["sothutu"],
                "tenhang": r["tenhang"],
                "soluong": r["soluong"],
                "page": r["page"],
                "pageName": r["pageName"]
            })

        return jsonify({"status": "success", "data": data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get_all_dates", methods=["GET"])
def get_all_dates():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ngay FROM dulieu ORDER BY ngay DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # convert tuple thành list string
    dates = [r[0].strftime("%Y-%m-%d") for r in rows]

    return jsonify({"success": True, "data": dates})

@app.route("/get_all_tenhang", methods=["GET"])
def get_all_tenhang():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT tenhang FROM dulieu ORDER BY tenhang ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # rows = [('Cá cơm',), ('Cá nục',)...]
    tenhang_list = [r[0] for r in rows]

    return jsonify({"success": True, "data": tenhang_list})

@app.route("/get_all_pageName", methods=["GET"])
def get_all_pageName():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT pageName FROM dulieu ORDER BY pageName ASC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # rows = [('Cá cơm',), ('Cá nục',)...]
    pageName_list = [r[0] for r in rows]

    return jsonify({"success": True, "data": pageName_list})

@app.route("/get_num_page_by_date", methods=["GET"])
def get_num_page_by_date():
    ngay = request.args.get("ngay")

    if not ngay:
        return jsonify({"success": False, "message": "Chưa truyền ngày", "data": []})

    conn = connect_db()
    cursor = conn.cursor()

    query = """
        SELECT DISTINCT page 
        FROM dulieu 
        WHERE ngay = %s
        ORDER BY page ASC
    """
    cursor.execute(query, (ngay,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    # Convert tuple -> int
    pages = [row[0] for row in rows]

    # Nếu không có dữ liệu —> giống code SQLite của Hên
    if len(pages) == 0:
        pages = [1]

    return jsonify({
        "success": True,
        "data": pages
    })


from datetime import datetime

def convert_ngay(ngay):
    ngay = ngay.strip()  # XOÁ MỌI KÝ TỰ THỪA

    # Nếu dạng yyyy-MM-dd => parse lại rồi format 100% chuẩn
    if "-" in ngay and len(ngay) == 10:
        return datetime.strptime(ngay, "%Y-%m-%d").strftime("%Y-%m-%d")

    # dd/MM/yyyy
    if "/" in ngay:
        return datetime.strptime(ngay, "%d/%m/%Y").strftime("%Y-%m-%d")

    # Aiven dạng: Sat, 03 Dec 2025 00:00:00 GMT
    if "," in ngay and "GMT" in ngay:
        return datetime.strptime(ngay, "%a, %d %b %Y %H:%M:%S GMT").strftime("%Y-%m-%d")

    # ISO
    if "T" in ngay:
        return datetime.strptime(ngay, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

    return ngay

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
