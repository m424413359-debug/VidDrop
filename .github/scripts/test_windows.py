"""
اختبار VidDrop.exe على Windows قبل النشر (يشغّله release.yml بعد البناء):
  1) البرنامج يفتح ولا ينهار
  2) التحديث كاملاً: تنزيل → استبدال الـ exe وهو شغّال → فتح النسخة الجديدة
المسار فيه مسافة وحروف عربية عمداً.
"""
import http.server
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import types

ROOT = os.getcwd()
BUILT = os.path.join(ROOT, "dist", "VidDrop.exe")
WORK = os.path.join(os.environ.get("RUNNER_TEMP", os.environ["TEMP"]), "اختبار VidDrop")
HOME = os.path.join(WORK, "home")
APP_DIR = os.path.join(WORK, "برامجي")
APP = os.path.join(APP_DIR, "VidDrop.exe")

shutil.rmtree(WORK, ignore_errors=True)
os.makedirs(HOME)
os.makedirs(APP_DIR)
shutil.copy2(BUILT, APP)
os.environ["USERPROFILE"] = HOME  # يجعل ~/.viddrop داخل مجلد الاختبار
sys.path.insert(0, ROOT)
import viddrop as v  # noqa: E402


def viddrop_pids():
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq VidDrop.exe", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return {int(line.split('","')[1]) for line in out.splitlines() if line.startswith('"VidDrop.exe"')}


def kill_all():
    subprocess.run(["taskkill", "/F", "/T", "/IM", "VidDrop.exe"], capture_output=True)


def fail(msg):
    kill_all()
    print("FAILED:", msg)
    sys.exit(1)


# 1) البرنامج يفتح ويبقى شغّالاً
proc = subprocess.Popen([APP], env={**os.environ})
time.sleep(25)
if proc.poll() is not None:
    fail(f"VidDrop.exe exited right after starting (code {proc.returncode})")
print("1) VidDrop.exe started and is still running after 25s")

# 2) تنزيل التحديث من سيرفر محلي
handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=os.path.dirname(BUILT), **kw)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
info = {"version": "99.0", "url": f"http://127.0.0.1:{srv.server_port}/VidDrop.exe",
        "size": os.path.getsize(BUILT), "notes": ""}

fake = types.SimpleNamespace(ui_events=queue.Queue(), t=lambda k, **kw: k, items=[],
                             on_close=lambda: None, on_update_event=lambda *a: fail(f"install_update: {a}"))
fake.update_paths = lambda i: v.VidDropApp.update_paths(fake, i)
v.VidDropApp._download_update_thread(fake, info)
events = []
while not fake.ui_events.empty():
    events.append(fake.ui_events.get())
final = [e for e in events if e[1] != "progress"]
if not final or final[-1][1] != "ready":
    fail(f"update download: {final}")
new_file = final[-1][2]
print("2) update downloaded to", new_file)

# 3) الاستبدال: نفس الأمر الذي ينفذه زر "أعد التشغيل الآن" بينما البرنامج القديم ما زال شغّالاً
old_pids = viddrop_pids()
os.environ["_PYI_ARCHIVE_FILE"] = APP  # كأننا داخل البرنامج المجمّد
fake.update_file = new_file
real_exe, sys.executable = sys.executable, APP
v.VidDropApp.install_update(fake)
sys.executable = real_exe
time.sleep(3)
subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)  # البرنامج القديم يُغلق

backup = os.path.splitext(APP)[0] + ".old.exe"
bat = os.path.join(v.UPDATE_DIR, "update.bat")
for _ in range(60):
    time.sleep(1)
    new_pids = viddrop_pids() - old_pids
    if not os.path.exists(new_file) and new_pids:
        break
else:
    fail(f"swap did not finish: new_file_left={os.path.exists(new_file)} "
         f"new_process={bool(viddrop_pids() - old_pids)} files={os.listdir(APP_DIR)}")
print("3) exe swapped and the new version launched")

time.sleep(20)
if not (viddrop_pids() - old_pids):
    fail("the relaunched VidDrop.exe did not stay running")
if os.path.exists(bat):
    fail("update.bat did not delete itself")
if os.path.getsize(APP) != os.path.getsize(BUILT):
    fail("VidDrop.exe has the wrong size after the swap")
if os.path.exists(backup):
    fail("the new version did not delete VidDrop.old.exe")
print("4) relaunched app still running after 20s; update.bat and VidDrop.old.exe were removed")

kill_all()
print("ALL WINDOWS TESTS PASSED")
