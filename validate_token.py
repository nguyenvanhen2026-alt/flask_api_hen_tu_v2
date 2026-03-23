
from flask import request, jsonify
from database import connect_db
def register_token(app):
    @app.route("/validate-token", methods=["POST"])
    def validate_token():

        data = request.get_json()

        token = data.get("token")

        conn = connect_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM device WHERE token=%s",
            (token,)
        )

        device = cur.fetchone()

        conn.close()

        if device:
            return jsonify({"valid":True})

        return jsonify({"valid":False})