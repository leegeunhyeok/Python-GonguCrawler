from PIL import Image
import urllib.request
import io

url = "https://www.google.co.kr/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"

def save():
    image = urllib.request.urlopen(url).read()
    out = io.BytesIO(image)
    save = io.BytesIO()
    img = Image.open(out)
    img.thumbnail((200, 200))
    # print(img.size())
    img.save("g.png")
    img.save(save, format="PNG")
    print(save.getvalue())

save()
