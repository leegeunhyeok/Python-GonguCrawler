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

# 네트워크에서 받아오자마자 저장하지 않고 인코딩
filedata = urllib.request.urlopen('https://www.google.co.kr/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png').read()

# Bytes 데이터 Insert
cur.execute("INSERT INTO test_blob VALUES (%s)", (filedata,))
conn.commit()

# 데이터 1개 불러오기
cur.execute("SELECT image FROM test_blob LIMIT 1")

file_data_2 = cur.fetchone()["image"]
print(file_data_2)

# 파일 쓰기
with open("blob.png", "wb") as f:
    f.write(file_data_2)
    print("디코딩 완료:", "blob.png")

cur.close()
conn.close()
