# يرسم أيقونة البرنامج (icon.ico) وصورة بدء التشغيل (splash.png) تلقائياً قبل بناء ملف exe
from PIL import Image, ImageDraw, ImageFont

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

# صورة تظهر أثناء فك ملفات VidDrop.exe (10-20 ثانية على الأجهزة الضعيفة) حتى لا يبدو البرنامج معطلاً
W, H = 420, 240
sp = Image.new("RGB", (W, H), (18, 19, 24))
sd = ImageDraw.Draw(sp)
sp.paste(img.resize((96, 96)), ((W - 96) // 2, 34), img.resize((96, 96)))


def font(size, bold=False):
    for name in (("segoeuib.ttf", "arialbd.ttf") if bold else ("segoeui.ttf", "arial.ttf")):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size)


sd.text((W // 2, 158), "VidDrop", font=font(30, True), fill="white", anchor="mm")
sd.text((W // 2, 200), "Starting…", font=font(15), fill=(156, 163, 175), anchor="mm")
sp.save("splash.png")
print("splash.png created")
