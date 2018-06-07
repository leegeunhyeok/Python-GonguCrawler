"""
Base64 해시 바이트 -> 문자열 변환
"""
import base64, zlib

# 원본 파일 명
file_name = "test.png"

# 디코딩하여 저장할 파일 명
decode_file_name = "test_decoded.png"

# 파일 읽고 Base64 인코딩
with open(file_name, "rb") as image:
    encoded = base64.b64encode(image.read())
    encoded_comp = zlib.compress(encoded)
    print("인코딩 데이터 길이:", len(encoded.decode("utf-8")))
    print("압축 데이터 길이(Bytes):", len(encoded_comp))
    print("압축 데이터 길이(String):", len(str(encoded_comp)))

# # Base64로 인코딩된 데이터를 다시 디코딩하여 저장
# image_data = base64.b64decode(zlib.decompress(encoded))
# with open(decode_file_name, "wb") as f:
#     f.write(image_data)
#     print("디코딩 완료:", decode_file_name)

