"""
Base64 해시 데이터 압축 테스트
"""
import urllib.request
import base64
from PIL import Image
import io
import pymysql

conn = pymysql.connect(host="localhost", port=3306, user="root", password="1234", db="python")
cur = conn.cursor(pymysql.cursors.DictCursor)

decode_file_name = "test_decoded.png"

# 네트워크에서 받아오자마자 저장하지 않고 인코딩
filedata_1 = urllib.request.urlopen('https://www.google.co.kr/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png').read()
hash1 = base64.b64encode(filedata_1).decode()

cur.execute("INSERT INTO test_decode VALUES (%s)", (hash1,))
conn.commit()

cur.execute("SELECT hash_ FROM test_decode LIMIT 1")
hash2 = cur.fetchone()["hash_"]

print(hash1 == hash2)

image_data = base64.b64decode(hash1.encode())
with open("1.png", "wb") as f:
    f.write(image_data.strip())
    print("디코딩 완료:", "1.png")

# DB에서 받아오면 String 타입
# String -> Bytes 타입으로 바꿔줘야함
image_data = base64.b64decode(hash2.encode())
with open("2.png", "wb") as f:
    f.write(image_data.strip())
    print("디코딩 완료:", "2.png")