from datetime import datetime

def convert_ngay(ngay):
    ngay = ngay.strip()

    if "-" in ngay and len(ngay) == 10:
        return datetime.strptime(ngay, "%Y-%m-%d").strftime("%Y-%m-%d")

    if "/" in ngay:
        return datetime.strptime(ngay, "%d/%m/%Y").strftime("%Y-%m-%d")

    if "," in ngay and "GMT" in ngay:
        return datetime.strptime(ngay,"%a, %d %b %Y %H:%M:%S GMT").strftime("%Y-%m-%d")

    if "T" in ngay:
        return datetime.strptime(ngay,"%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d")

    return ngay