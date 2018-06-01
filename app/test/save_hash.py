import base64

with open("test2.png", "rb") as image:
    hash = base64.b64encode(image.read())

    with open("test.txt", "w") as txt:
        txt.write(str(hash))