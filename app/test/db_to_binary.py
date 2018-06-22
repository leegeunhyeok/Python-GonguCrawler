import urllib.request
import base64
from PIL import Image
import io
import pymysql
import zlib

conn = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="python")
cur = conn.cursor(pymysql.cursors.DictCursor)

cur.execute("SELECT hash_ FROM test_decode_compress")
result = cur.fetchone()["hash_"]

with open("db_.png", "wb") as img:
    img.write(base64.b64decode(zlib.decompress(result)))
    print("변환 완료")