"""
Base64 해시 데이터 텍스트 저장 테스트
"""
import base64

with open("test2.png", "rb") as image:
    hash = base64.b64encode(image.read())

    with open("test.txt", "w") as txt:
        txt.write(str(hash))