# يرسم أيقونة البرنامج (icon.ico) تلقائياً قبل بناء ملف exe
from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([8, 8, S - 8, S - 8], radius=56, fill=(124, 92, 255))
# سهم تحميل
d.rectangle([108, 52, 148, 140], fill="white")
d.polygon([(70, 128), (186, 128), (128, 190)], fill="white")
d.rounded_rectangle([64, 200, 192, 214], radius=7, fill="white")
img.save("icon.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon.ico created")
