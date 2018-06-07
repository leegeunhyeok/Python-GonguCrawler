"""
Base64 해시 데이터 압축 테스트
"""
import urllib.request
import base64
from PIL import Image
import io
import pymysql
import zlib

conn = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="python")
cur = conn.cursor(pymysql.cursors.DictCursor)

decode_file_name = "test_decoded.png"

# 네트워크에서 받아오자마자 저장하지 않고 인코딩
filedata_1 = urllib.request.urlopen('https://www.google.co.kr/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png').read()
hash1 = zlib.compress(base64.b64encode(filedata_1))

cur.execute("INSERT INTO test_decode_compress VALUES (%s)", (hash1,))
conn.commit()

cur.execute("SELECT hash_ FROM test_decode_compress LIMIT 1")
hash2 = cur.fetchone()["hash_"]

print(hash1 == hash2)

# 변환한 데이터로 쓰기
image_data = base64.b64decode(zlib.decompress(hash1))
with open("1.png", "wb") as f:
    f.write(image_data.strip())
    print("디코딩 완료:", "1.png")

# DB에 있던 데이터로 쓰기
image_data = base64.b64decode(zlib.decompress(hash2))
with open("2.png", "wb") as f:
    f.write(image_data.strip())
    print("디코딩 완료:", "2.png")