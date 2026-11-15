"""
يقرر ماذا يفعل release.yml في هذا التشغيل، ويكتب النتيجة في GITHUB_OUTPUT:
  build   = true  ← ابنِ VidDrop.exe واختبره
  publish = true  ← انشره كـ Release (ينشئ الـ tag)
  bump    = true  ← (الفحص الأسبوعي) صدر yt-dlp جديد: ارفع رقم النسخة وأضف سطراً في CHANGELOG

القواعد:
  • pull request: بناء واختبار فقط
  • push على main / tag / تشغيل يدوي: انشر إذا لم يكن لرقم APP_VERSION الحالي Release بعد
  • الفحص الأسبوعي (schedule): نفس القاعدة، وإن كان الـ Release موجوداً وصدر yt-dlp أحدث من
    الموجود داخل آخر نسخة ← نسخة جديدة برقم فرعي (1.3 ← 1.3.1 ← 1.3.2 …)
"""
import json
import os
import re
import subprocess
import sys
import urllib.request

EVENT = os.environ["GITHUB_EVENT_NAME"]
REF = os.environ.get("GITHUB_REF", "")


def nums(v):
    return tuple(int(n) for n in re.findall(r"\d+", v or ""))


def release_body(tag=None):
    """نص الـ Release (الأخير إن لم يُحدد tag)، أو None إن لم يكن موجوداً."""
    cmd = ["gh", "release", "view"] + ([tag] if tag else []) + ["--json", "body", "--jq", ".body"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return r.stdout if r.returncode == 0 else None


src = open("viddrop.py", encoding="utf-8", newline="").read()
m = re.search(r'^APP_VERSION = "([^"]+)"', src, re.M)
if not m:
    sys.exit("::error::APP_VERSION not found in viddrop.py")
version = m.group(1)
tag = "v" + version
if REF.startswith("refs/tags/") and REF != "refs/tags/" + tag:
    sys.exit(f"::error::Tag {REF[10:]} does not match APP_VERSION = {version}")

exists = release_body(tag) is not None
is_pr = EVENT == "pull_request"
publish = not is_pr and not exists
bump = False

if EVENT == "schedule" and exists:
    with urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json", timeout=30) as r:
        latest = json.load(r)["info"]["version"]
    bundled = re.search(r"^yt-dlp (\S+)", release_body() or "", re.M)
    print(f"yt-dlp: latest on PyPI {latest} | inside the latest release {bundled.group(1) if bundled else 'unknown'}")
    if not bundled or nums(latest) > nums(bundled.group(1)):
        parts = list(nums(version)) + [0] * (3 - len(nums(version)))
        parts[2] += 1
        version = ".".join(map(str, parts))
        tag = "v" + version
        src = src.replace(m.group(0), f'APP_VERSION = "{version}"')
        open("viddrop.py", "w", encoding="utf-8", newline="").write(src)
        log = open("CHANGELOG.txt", encoding="utf-8", newline="").read()
        nl = "\r\n" if "\r\n" in log else "\n"
        entry = f"{tag}{nl}- تحديث yt-dlp إلى {latest} (إصلاحات التحميل من يوتيوب والمواقع الأخرى){nl}{nl}"
        first = re.search(r"^v\d", log, re.M)
        log = log[:first.start()] + entry + log[first.start():]
        open("CHANGELOG.txt", "w", encoding="utf-8", newline="").write(log)
        publish = bump = True

out = {"version": version, "tag": tag, "build": is_pr or publish, "publish": publish, "bump": bump}
with open(os.environ["GITHUB_OUTPUT"], "a") as f:
    for k, v in out.items():
        f.write(f"{k}={str(v).lower() if isinstance(v, bool) else v}\n")
print(f"event {EVENT} | release {tag} exists: {exists} |", out)
