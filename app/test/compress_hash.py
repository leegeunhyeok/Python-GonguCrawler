"""
Base64 해시 데이터 압축 테스트
"""
import base64, zlib

# 원본 파일 명
file_name = "test.png"

# 파일 읽고 Base64 인코딩
with open(file_name, "rb") as image:
    encoded = base64.b64encode(image.read())
    compressed = zlib.compress(encoded)
    print("원본 데이터 길이:", len(encoded))
    print("압축 데이터 길이:", len(compressed))
    print("압축 해제 후 데이터 길이:", len(zlib.decompress(compressed)))

with open("compressed_" + file_name, "wb") as image:
    # 압축 해제 후 Base64 디코딩
    image.write(base64.b64decode(zlib.decompress(compressed)))