import pymysql
import os

def connect_db():
    return pymysql.connect(
        host=os.environ.get("AIVEN_HOST"),
        user=os.environ.get("AIVEN_USER"),
        password=os.environ.get("AIVEN_PASS"),
        database=os.environ.get("AIVEN_DB"),
        port=int(os.environ.get("AIVEN_PORT")),
        ssl={"ca": os.path.join(os.path.dirname(__file__), "ca.pem")}

        # ❌ tắt SSL tạm
        # ssl={"ca": "ca.pem"}
    )