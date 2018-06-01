import base64

# 원본 파일 명
file_name = "test.png"

# 디코딩하여 저장할 파일 명
decode_file_name = "test_decoded.png"

# 파일 읽고 Base64 인코딩
with open(file_name, "rb") as image:
    encoded = str(base64.b64encode(image.read()))

encoded = encoded[2:-1]

# Base64로 인코딩된 데이터를 다시 디코딩하여 저장
image_data = base64.b64decode(encoded.encode())
with open(decode_file_name, "wb") as f:
    f.write(image_data)
    print("디코딩 완료:", decode_file_name)

