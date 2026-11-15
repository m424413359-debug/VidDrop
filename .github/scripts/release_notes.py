"""يكتب notes.md للـ Release: سطور النسخة من CHANGELOG + طريقة التشغيل + رقم yt-dlp الموجود داخل الـ exe."""
import re
import sys

import yt_dlp.version

tag = sys.argv[1]
notes, inside = [], False
for line in open("CHANGELOG.txt", encoding="utf-8").read().splitlines():
    if re.match(r"^v\d", line.strip()):
        inside = line.strip() == tag
    elif inside:
        notes.append(line)
text = "\n".join(notes).strip() or "VidDrop " + tag
text += f"""

---
**طريقة التشغيل:** نزّل `VidDrop.exe` وشغّله — لا يحتاج تثبيتاً ولا Python.
- إذا ظهرت رسالة "Windows protected your PC": اضغط **More info** ثم **Run anyway** (البرنامج غير موقّع رقمياً).
- ضع الملف في مجلد عادي مثل سطح المكتب (ليس داخل Program Files) حتى يعمل التحديث التلقائي.
- في أول تشغيل ينزّل البرنامج مكوّن يوتيوب (Deno، حوالي 40 MB) مرة واحدة.
- يعمل على Windows 10 و 11 (64-bit).

yt-dlp {yt_dlp.version.__version__}
"""
open("notes.md", "w", encoding="utf-8").write(text)
print(text)
