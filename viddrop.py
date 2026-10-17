"""
VidDrop — واجهة رسومية أنيقة لأداة yt-dlp
A modern GUI for yt-dlp (CustomTkinter)

الميزات:
  • جلب معلومات الفيديو (العنوان، الصورة المصغرة، المدة) واختيار الجودة
  • الترجمة: بدون / أصلية / تلقائية (مترجمة آلياً) + اللغة + الصيغة + طريقة الحفظ
  • قائمة انتظار تتحمّل بالترتيب مع إيقاف واستئناف
  • استئناف تلقائي عند انقطاع الإنترنت، وحفظ القائمة عند إغلاق البرنامج
  • مراقبة الحافظة: انسخ رابطاً من المتصفح فيظهر لك اقتراح التحميل
  • واجهة عربية / إنجليزية، ووضع داكن / فاتح
"""

import io
import json
import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import uuid
from tkinter import filedialog, TclError

import customtkinter as ctk
from PIL import Image
import yt_dlp
from yt_dlp.utils import DownloadCancelled, DownloadError

# ─────────────────────────── إعدادات عامة ───────────────────────────

APP_NAME = "VidDrop"
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".viddrop")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")
QUEUE_FILE = os.path.join(CONFIG_DIR, "queue.json")
DEFAULT_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads", "VidDrop")

ACCENT = "#7C5CFF"
ACCENT_HOVER = "#6747F5"
SUCCESS = "#22C55E"
DANGER = "#EF4444"
WARNING = "#F59E0B"
MUTED = ("#6B7280", "#9CA3AF")
CARD = ("#FFFFFF", "#1C1D24")
CARD_2 = ("#F3F4F8", "#24252E")
BG = ("#EEF0F5", "#121318")

FONT_FAMILY = "Segoe UI" if sys.platform.startswith("win") else None

DEFAULT_SETTINGS = {
    "language": "ar",
    "appearance": "dark",
    "folder": DEFAULT_FOLDER,
    "clipboard": True,
    "queue_running": True,
    "quick_quality": "1080",
}

# ─────────────────────────── النصوص (عربي / إنجليزي) ───────────────────────────

TEXTS = {
    "ar": {
        "subtitle": "حمّل فيديوهاتك بالجودة التي تريدها — بسهولة",
        "link": "رابط الفيديو",
        "url_ph": "الصق رابط الفيديو هنا…",
        "paste": "لصق",
        "fetch": "جلب المعلومات",
        "fetching": "جارٍ جلب المعلومات…",
        "options": "خيارات التحميل",
        "quality": "الجودة",
        "best": "أفضل جودة متاحة",
        "audio": "صوت فقط (MP3)",
        "subs": "الترجمة",
        "sub_none": "بدون",
        "sub_manual": "أصلية",
        "sub_auto": "تلقائية / آلية",
        "sub_lang": "اللغة",
        "sub_fmt": "الصيغة",
        "sub_mode": "طريقة الحفظ",
        "mode_file": "ملف منفصل",
        "mode_embed": "داخل الفيديو",
        "mode_both": "الاثنين",
        "no_subs": "لا توجد ترجمة من هذا النوع",
        "save_to": "مكان الحفظ",
        "browse": "تغيير",
        "add": "⬇   أضف إلى التحميل",
        "queue": "قائمة التحميل",
        "empty": "لا توجد تحميلات بعد.\nالصق رابطاً، أو انسخه من المتصفح وسيظهر هنا اقتراح.",
        "clip": "مراقبة الحافظة",
        "pause_all": "إيقاف القائمة",
        "resume_all": "تشغيل القائمة",
        "clear_done": "مسح المكتمل",
        "st_pending": "في الانتظار",
        "st_downloading": "جارٍ التحميل",
        "st_processing": "جارٍ المعالجة (دمج / تحويل)…",
        "st_done": "اكتمل ✓",
        "st_error": "فشل: {e}",
        "st_paused": "متوقف مؤقتاً",
        "st_retry": "انقطع الاتصال — محاولة جديدة خلال {s} ث",
        "st_offline": "لا يوجد إنترنت — بانتظار عودة الاتصال…",
        "st_queue_off": "القائمة متوقفة",
        "pause": "إيقاف",
        "resume": "استئناف",
        "remove": "حذف",
        "retry": "إعادة",
        "open": "فتح المجلد",
        "detected": "رابط جديد في الحافظة",
        "details": "عرض الخيارات",
        "quick": "تحميل سريع",
        "ignore": "تجاهل",
        "invalid": "الرابط غير صالح",
        "fetch_fail": "تعذّر جلب المعلومات: {e}",
        "playlist": "هذا رابط قائمة تشغيل — الإصدار الحالي يدعم الفيديو الواحد.",
        "ffmpeg_missing": "تنبيه: FFmpeg غير موجود — الجودات العالية وتحويل MP3 ودمج الترجمة لن تعمل.",
        "deno_missing": "تنبيه: Deno غير مثبّت — قد لا تظهر كل الجودات من يوتيوب. شغّل setup.bat",
        "progress": "{p}   •   {speed}   •   متبقٍ {eta}",
        "duration": "المدة",
        "added": "✓ أُضيف إلى القائمة",
        "count": "{n} عنصر",
        "lang_btn": "English",
        "dark": "داكن",
        "light": "فاتح",
    },
    "en": {
        "subtitle": "Download your videos in the quality you want — effortlessly",
        "link": "Video link",
        "url_ph": "Paste a video link here…",
        "paste": "Paste",
        "fetch": "Fetch info",
        "fetching": "Fetching info…",
        "options": "Download options",
        "quality": "Quality",
        "best": "Best available",
        "audio": "Audio only (MP3)",
        "subs": "Subtitles",
        "sub_none": "None",
        "sub_manual": "Original",
        "sub_auto": "Auto / translated",
        "sub_lang": "Language",
        "sub_fmt": "Format",
        "sub_mode": "Save as",
        "mode_file": "Separate file",
        "mode_embed": "Inside video",
        "mode_both": "Both",
        "no_subs": "No subtitles of this type",
        "save_to": "Save to",
        "browse": "Change",
        "add": "⬇   Add to downloads",
        "queue": "Downloads",
        "empty": "No downloads yet.\nPaste a link, or copy one in your browser and a suggestion will pop up.",
        "clip": "Watch clipboard",
        "pause_all": "Pause queue",
        "resume_all": "Start queue",
        "clear_done": "Clear finished",
        "st_pending": "Waiting",
        "st_downloading": "Downloading",
        "st_processing": "Processing (merge / convert)…",
        "st_done": "Completed ✓",
        "st_error": "Failed: {e}",
        "st_paused": "Paused",
        "st_retry": "Connection lost — retrying in {s}s",
        "st_offline": "No internet — waiting for connection…",
        "st_queue_off": "Queue paused",
        "pause": "Pause",
        "resume": "Resume",
        "remove": "Remove",
        "retry": "Retry",
        "open": "Open folder",
        "detected": "New link in clipboard",
        "details": "Show options",
        "quick": "Quick download",
        "ignore": "Ignore",
        "invalid": "Invalid link",
        "fetch_fail": "Couldn't fetch info: {e}",
        "playlist": "This is a playlist link — this version supports single videos.",
        "ffmpeg_missing": "Warning: FFmpeg not found — high qualities, MP3 and embedded subtitles won't work.",
        "deno_missing": "Warning: Deno is not installed — some YouTube qualities may be missing. Run setup.bat",
        "progress": "{p}   •   {speed}   •   {eta} left",
        "duration": "Duration",
        "added": "✓ Added to downloads",
        "count": "{n} items",
        "lang_btn": "عربي",
        "dark": "Dark",
        "light": "Light",
    },
}

# ─────────────────────────── أدوات مساعدة ───────────────────────────


def find_ffmpeg():
    """يبحث عن FFmpeg في النظام، وإن لم يجده يستخدم النسخة المرفقة مع imageio-ffmpeg."""
    path = shutil.which("ffmpeg")
    if path:
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def is_online(timeout=3):
    for host in (("1.1.1.1", 53), ("8.8.8.8", 53)):
        try:
            socket.create_connection(host, timeout=timeout).close()
            return True
        except OSError:
            continue
    return False


NETWORK_HINTS = (
    "timed out", "timeout", "temporary failure", "getaddrinfo", "connection",
    "network", "unreachable", "remote end closed", "incompleteread",
    "10054", "10060", "11001", "errno 104", "ssl", "http error 5",
)


def looks_like_network_error(msg):
    m = msg.lower()
    return any(h in m for h in NETWORK_HINTS)


def fmt_bytes(n):
    if not n:
        return "—"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def fmt_time(sec):
    if sec is None:
        return "—"
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def shorten(text, n):
    text = text or ""
    return text if len(text) <= n else text[: n - 1] + "…"


def clean_error(msg):
    msg = re.sub(r"\x1b\[[0-9;]*m", "", str(msg))
    msg = msg.replace("ERROR:", "").strip()
    return shorten(msg.splitlines()[0] if msg else "", 90)


def open_in_explorer(path):
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(path):
                subprocess.Popen(f'explorer /select,"{os.path.normpath(path)}"')
            else:
                os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path] if os.path.isfile(path) else ["open", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path) if os.path.isfile(path) else path])
    except Exception:
        pass


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass


class _QuietLogger:
    """يمنع yt-dlp من طباعة الرسائل في الطرفية ويحتفظ بآخر خطأ."""

    def __init__(self):
        self.last_error = ""

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        self.last_error = msg


class StopRequested(DownloadCancelled):
    msg = "stopped by user"


# ─────────────────────────── نموذج عنصر التحميل ───────────────────────────


class Item:
    def __init__(self, url, title, opts, status="pending", filepath="", error="", id=None):
        self.id = id or uuid.uuid4().hex[:10]
        self.url = url
        self.title = title or url
        self.opts = opts           # quality / sub_type / sub_lang / sub_fmt / sub_mode / folder
        self.status = status       # pending, downloading, processing, done, error, paused, retry, offline
        self.filepath = filepath
        self.error = error
        self.progress = 1.0 if status == "done" else 0.0
        self.speed = None
        self.eta = None
        self.retry_in = 0
        self.stop_reason = None    # "pause" | "remove"
        self.widgets = {}

    def to_dict(self):
        status = self.status
        if status in ("downloading", "processing", "retry", "offline"):
            status = "pending"  # عند فتح البرنامج من جديد يكمل من حيث توقف
        return {"id": self.id, "url": self.url, "title": self.title, "opts": self.opts,
                "status": status, "filepath": self.filepath, "error": self.error}


# ─────────────────────────── التطبيق ───────────────────────────


class VidDropApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.settings = {**DEFAULT_SETTINGS, **load_json(SETTINGS_FILE, {})}
        ctk.set_appearance_mode(self.settings["appearance"])
        ctk.set_default_color_theme("blue")

        self.title(APP_NAME)
        self.geometry("1180x740")
        self.minsize(1000, 640)
        self.configure(fg_color=BG)

        self.ffmpeg = find_ffmpeg()
        self.has_deno = shutil.which("deno") is not None

        # الحالة
        self.items = [Item(**d) for d in load_json(QUEUE_FILE, []) if d.get("url")]
        self.current_url = ""
        self.current_info = None
        self.quality_map = {}
        self.ui_events = queue.Queue()
        self.dirty = set()
        self.queue_dirty = False
        self.wake = threading.Event()
        self.last_clip = None
        self.extractors = None
        self.toast = None
        self.thumb_image = None

        self.build_ui()
        self.wake.set()

        threading.Thread(target=self.worker_loop, daemon=True).start()
        threading.Thread(target=self._load_extractors, daemon=True).start()
        self.after(120, self.poll_events)
        self.after(1200, self.poll_clipboard)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ───── أدوات ─────

    def t(self, key, **kw):
        s = TEXTS[self.settings["language"]].get(key, key)
        return s.format(**kw) if kw else s

    @property
    def rtl(self):
        return self.settings["language"] == "ar"

    @property
    def side(self):
        return "right" if self.rtl else "left"

    @property
    def opp(self):
        return "left" if self.rtl else "right"

    @property
    def anchor(self):
        return "e" if self.rtl else "w"

    def font(self, size=13, weight="normal"):
        return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)

    def save_settings(self):
        save_json(SETTINGS_FILE, self.settings)

    def save_queue(self):
        save_json(QUEUE_FILE, [i.to_dict() for i in self.items])

    def card(self, master, **kw):
        return ctk.CTkFrame(master, fg_color=CARD, corner_radius=16, **kw)

    def section_title(self, master, text):
        ctk.CTkLabel(master, text=text, font=self.font(15, "bold"), anchor=self.anchor).pack(
            fill="x", padx=18, pady=(14, 6))

    def field_label(self, master, text):
        ctk.CTkLabel(master, text=text, font=self.font(12), text_color=MUTED,
                     anchor=self.anchor).pack(fill="x", padx=18, pady=(8, 2))

    # ───── بناء الواجهة ─────

    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()
        self.toast = None
        for it in self.items:
            it.widgets = {}

        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=20, pady=16)

        self._build_header(root)

        body = ctk.CTkFrame(root, fg_color="transparent")
        body.pack(fill="both", expand=True, pady=(14, 0))
        left_col, right_col = (1, 0) if self.rtl else (0, 1)
        body.grid_columnconfigure(left_col, weight=5, uniform="c")
        body.grid_columnconfigure(right_col, weight=6, uniform="c")
        body.grid_rowconfigure(0, weight=1)

        form = ctk.CTkScrollableFrame(body, fg_color="transparent")
        form.grid(row=0, column=left_col, sticky="nsew",
                  padx=(0, 8) if not self.rtl else (8, 0))
        self._build_form(form)

        qcard = self.card(body)
        qcard.grid(row=0, column=right_col, sticky="nsew",
                   padx=(8, 0) if not self.rtl else (0, 8))
        self._build_queue(qcard)

        self.refresh_form()
        self.rebuild_queue_cards()

    def _build_header(self, root):
        head = ctk.CTkFrame(root, fg_color="transparent")
        head.pack(fill="x")

        logo = ctk.CTkFrame(head, fg_color=ACCENT, corner_radius=14, width=48, height=48)
        logo.pack(side=self.side)
        logo.pack_propagate(False)
        ctk.CTkLabel(logo, text="⬇", font=self.font(24, "bold"), text_color="white").pack(expand=True)

        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.pack(side=self.side, padx=12)
        ctk.CTkLabel(titles, text=APP_NAME, font=self.font(24, "bold"), anchor=self.anchor).pack(fill="x")
        ctk.CTkLabel(titles, text=self.t("subtitle"), font=self.font(12), text_color=MUTED,
                     anchor=self.anchor).pack(fill="x")

        ctk.CTkButton(head, text=self.t("lang_btn"), width=90, height=34, corner_radius=10,
                      fg_color=CARD_2, text_color=("#111", "#EEE"), hover_color=("#E2E4EC", "#30313C"),
                      font=self.font(13, "bold"), command=self.toggle_language).pack(side=self.opp)

        self.theme_seg = ctk.CTkSegmentedButton(
            head, values=[self.t("dark"), self.t("light")], font=self.font(12),
            selected_color=ACCENT, selected_hover_color=ACCENT_HOVER, command=self.on_theme)
        self.theme_seg.set(self.t("dark") if self.settings["appearance"] == "dark" else self.t("light"))
        self.theme_seg.pack(side=self.opp, padx=10)

        warnings = []
        if not self.ffmpeg:
            warnings.append(self.t("ffmpeg_missing"))
        if not self.has_deno:
            warnings.append(self.t("deno_missing"))
        for w in warnings:
            ctk.CTkLabel(root, text=w, font=self.font(12), text_color=WARNING,
                         anchor=self.anchor).pack(fill="x", pady=(8, 0))

    def _build_form(self, form):
        # بطاقة الرابط
        c1 = self.card(form)
        c1.pack(fill="x", pady=(0, 12))
        self.section_title(c1, self.t("link"))

        row = ctk.CTkFrame(c1, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 6))
        self.url_entry = ctk.CTkEntry(row, placeholder_text=self.t("url_ph"), height=42,
                                      corner_radius=10, font=self.font(13))
        self.url_entry.pack(side=self.side, fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda e: self.fetch_info())
        if self.current_url:
            self.url_entry.insert(0, self.current_url)
        ctk.CTkButton(row, text=self.t("paste"), width=70, height=42, corner_radius=10,
                      fg_color=CARD_2, text_color=("#111", "#EEE"), hover_color=("#E2E4EC", "#30313C"),
                      font=self.font(13), command=self.paste_url).pack(side=self.side, padx=8)

        self.fetch_btn = ctk.CTkButton(c1, text=self.t("fetch"), height=40, corner_radius=10,
                                       fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                       font=self.font(14, "bold"), command=self.fetch_info)
        self.fetch_btn.pack(fill="x", padx=18, pady=(4, 6))
        self.form_msg = ctk.CTkLabel(c1, text="", font=self.font(12), text_color=MUTED,
                                     anchor=self.anchor, wraplength=420,
                                     justify="right" if self.rtl else "left")
        self.form_msg.pack(fill="x", padx=18, pady=(0, 6))

        # المعاينة
        self.preview = ctk.CTkFrame(c1, fg_color=CARD_2, corner_radius=12)
        self.thumb_label = ctk.CTkLabel(self.preview, text="", width=176, height=99,
                                        fg_color=("#DDE0E8", "#2E2F3A"), corner_radius=8)
        self.thumb_label.pack(side=self.side, padx=10, pady=10)
        info_box = ctk.CTkFrame(self.preview, fg_color="transparent")
        info_box.pack(side=self.side, fill="both", expand=True, padx=(0, 10), pady=10)
        self.pv_title = ctk.CTkLabel(info_box, text="", font=self.font(14, "bold"), anchor=self.anchor,
                                     wraplength=250, justify="right" if self.rtl else "left")
        self.pv_title.pack(fill="x")
        self.pv_meta = ctk.CTkLabel(info_box, text="", font=self.font(12), text_color=MUTED,
                                    anchor=self.anchor)
        self.pv_meta.pack(fill="x", pady=(6, 0))

        # بطاقة الخيارات
        self.opt_card = self.card(form)
        self.opt_card.pack(fill="x", pady=(0, 12))
        oc = self.opt_card
        self.section_title(oc, self.t("options"))

        self.field_label(oc, self.t("quality"))
        self.quality_menu = ctk.CTkOptionMenu(oc, values=[self.t("best")], height=38, corner_radius=10,
                                              fg_color=CARD_2, button_color=ACCENT,
                                              button_hover_color=ACCENT_HOVER, text_color=("#111", "#EEE"),
                                              font=self.font(13), dropdown_font=self.font(13),
                                              command=lambda _: self.update_sub_state())
        self.quality_menu.pack(fill="x", padx=18)

        self.field_label(oc, self.t("subs"))
        self.sub_keys = ["none", "manual", "auto"]
        sub_vals = [self.t("sub_none"), self.t("sub_manual"), self.t("sub_auto")]
        self.sub_seg = ctk.CTkSegmentedButton(oc, values=sub_vals, font=self.font(13), height=34,
                                              selected_color=ACCENT, selected_hover_color=ACCENT_HOVER,
                                              command=lambda _: self.update_sub_options())
        self.sub_seg.set(self.t("sub_none"))
        self.sub_seg.pack(fill="x", padx=18)

        self.sub_box = ctk.CTkFrame(oc, fg_color="transparent")
        self.sub_box.pack(fill="x")
        grid = ctk.CTkFrame(self.sub_box, fg_color="transparent")
        grid.pack(fill="x", padx=18, pady=(8, 0))
        lang_col, fmt_col = (1, 0) if self.rtl else (0, 1)
        grid.grid_columnconfigure(lang_col, weight=3)
        grid.grid_columnconfigure(fmt_col, weight=1)
        ctk.CTkLabel(grid, text=self.t("sub_lang"), font=self.font(12), text_color=MUTED,
                     anchor=self.anchor).grid(row=0, column=lang_col, sticky="ew")
        ctk.CTkLabel(grid, text=self.t("sub_fmt"), font=self.font(12), text_color=MUTED,
                     anchor=self.anchor).grid(row=0, column=fmt_col, sticky="ew", padx=8)
        self.lang_menu = ctk.CTkOptionMenu(grid, values=["—"], height=36, corner_radius=10,
                                           fg_color=CARD_2, button_color=ACCENT,
                                           button_hover_color=ACCENT_HOVER, text_color=("#111", "#EEE"),
                                           font=self.font(13), dropdown_font=self.font(12))
        self.lang_menu.grid(row=1, column=lang_col, sticky="ew")
        self.fmt_menu = ctk.CTkOptionMenu(grid, values=["SRT", "VTT", "ASS"], height=36, width=90,
                                          corner_radius=10, fg_color=CARD_2, button_color=ACCENT,
                                          button_hover_color=ACCENT_HOVER, text_color=("#111", "#EEE"),
                                          font=self.font(13))
        self.fmt_menu.grid(row=1, column=fmt_col, sticky="ew", padx=8)

        ctk.CTkLabel(self.sub_box, text=self.t("sub_mode"), font=self.font(12), text_color=MUTED,
                     anchor=self.anchor).pack(fill="x", padx=18, pady=(8, 2))
        self.mode_keys = ["file", "embed", "both"]
        self.mode_seg = ctk.CTkSegmentedButton(
            self.sub_box, values=[self.t("mode_file"), self.t("mode_embed"), self.t("mode_both")],
            font=self.font(13), height=34, selected_color=ACCENT, selected_hover_color=ACCENT_HOVER)
        self.mode_seg.set(self.t("mode_file"))
        self.mode_seg.pack(fill="x", padx=18)

        self.field_label(oc, self.t("save_to"))
        frow = ctk.CTkFrame(oc, fg_color=CARD_2, corner_radius=10)
        frow.pack(fill="x", padx=18)
        self.folder_label = ctk.CTkLabel(frow, text=shorten(self.settings["folder"], 48),
                                         font=self.font(12), anchor="w")
        self.folder_label.pack(side=self.side, fill="x", expand=True, padx=10, pady=6)
        ctk.CTkButton(frow, text=self.t("browse"), width=70, height=30, corner_radius=8,
                      fg_color=ACCENT, hover_color=ACCENT_HOVER, font=self.font(12),
                      command=self.choose_folder).pack(side=self.opp, padx=6, pady=6)

        self.add_btn = ctk.CTkButton(oc, text=self.t("add"), height=48, corner_radius=12,
                                     fg_color=ACCENT, hover_color=ACCENT_HOVER,
                                     font=self.font(16, "bold"), command=self.add_current)
        self.add_btn.pack(fill="x", padx=18, pady=(16, 18))

    def _build_queue(self, qcard):
        top = ctk.CTkFrame(qcard, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(14, 4))
        ctk.CTkLabel(top, text=self.t("queue"), font=self.font(15, "bold")).pack(side=self.side)
        self.count_label = ctk.CTkLabel(top, text="", font=self.font(12), text_color=MUTED)
        self.count_label.pack(side=self.side, padx=10)

        self.clip_var = ctk.BooleanVar(value=self.settings["clipboard"])
        ctk.CTkSwitch(top, text=self.t("clip"), variable=self.clip_var, font=self.font(12),
                      progress_color=ACCENT, command=self.on_clip_toggle).pack(side=self.opp)

        bar = ctk.CTkFrame(qcard, fg_color="transparent")
        bar.pack(fill="x", padx=18, pady=(2, 8))
        self.run_btn = ctk.CTkButton(bar, text="", width=120, height=30, corner_radius=8,
                                     font=self.font(12), command=self.toggle_queue)
        self.run_btn.pack(side=self.side)
        ctk.CTkButton(bar, text=self.t("clear_done"), width=110, height=30, corner_radius=8,
                      fg_color=CARD_2, text_color=("#111", "#EEE"), hover_color=("#E2E4EC", "#30313C"),
                      font=self.font(12), command=self.clear_done).pack(side=self.side, padx=8)
        self.update_run_btn()

        self.queue_frame = ctk.CTkScrollableFrame(qcard, fg_color="transparent")
        self.queue_frame.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self.empty_label = ctk.CTkLabel(self.queue_frame, text=self.t("empty"), font=self.font(13),
                                        text_color=MUTED, justify="center")

    # ───── بطاقات قائمة التحميل ─────

    def rebuild_queue_cards(self):
        for it in self.items:
            if it.widgets.get("card"):
                it.widgets["card"].destroy()
            it.widgets = {}
        for it in self.items:
            self.create_item_card(it)
        self.update_queue_meta()

    def create_item_card(self, it):
        cardf = ctk.CTkFrame(self.queue_frame, fg_color=CARD_2, corner_radius=12)
        cardf.pack(fill="x", padx=6, pady=5)
        w = {"card": cardf}

        top = ctk.CTkFrame(cardf, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))
        w["title"] = ctk.CTkLabel(top, text=shorten(it.title, 58), font=self.font(13, "bold"),
                                  anchor=self.anchor)
        w["title"].pack(side=self.side, fill="x", expand=True)
        w["badge"] = ctk.CTkLabel(top, text=self.quality_badge(it), font=self.font(11, "bold"),
                                  fg_color=ACCENT, text_color="white", corner_radius=6, width=60, height=22)
        w["badge"].pack(side=self.opp)

        w["bar"] = ctk.CTkProgressBar(cardf, height=8, corner_radius=4, progress_color=ACCENT)
        w["bar"].pack(fill="x", padx=12, pady=4)

        bottom = ctk.CTkFrame(cardf, fg_color="transparent")
        bottom.pack(fill="x", padx=12, pady=(2, 10))
        w["status"] = ctk.CTkLabel(bottom, text="", font=self.font(12), text_color=MUTED, anchor=self.anchor)
        w["status"].pack(side=self.side, fill="x", expand=True)
        w["btns"] = ctk.CTkFrame(bottom, fg_color="transparent")
        w["btns"].pack(side=self.opp)
        it.widgets = w
        self.update_item_card(it)

    def quality_badge(self, it):
        q = it.opts.get("quality")
        if q == "audio":
            return "MP3"
        if q == "best":
            return "BEST"
        return f"{q}p"

    def small_btn(self, master, text, cmd, color=None):
        b = ctk.CTkButton(master, text=text, width=64, height=26, corner_radius=7, font=self.font(11),
                          fg_color=color or ("#D9DCE6", "#363746"), text_color=("#111", "#EEE") if not color else "white",
                          hover_color=("#C9CCD8", "#44455A"), command=cmd)
        b.pack(side=self.opp, padx=3)
        return b

    def update_item_card(self, it):
        w = it.widgets
        if not w:
            return
        st = it.status
        bar = w["bar"]
        bar.set(max(0.0, min(1.0, it.progress)))
        color = {"done": SUCCESS, "error": DANGER, "paused": WARNING,
                 "retry": WARNING, "offline": WARNING}.get(st, ACCENT)
        bar.configure(progress_color=color)

        if st == "downloading":
            txt = self.t("progress", p=f"{it.progress * 100:.1f}%",
                         speed=(fmt_bytes(it.speed) + "/s") if it.speed else "—", eta=fmt_time(it.eta))
        elif st == "error":
            txt = self.t("st_error", e=it.error)
        elif st == "retry":
            txt = self.t("st_retry", s=it.retry_in)
        elif st == "offline":
            txt = self.t("st_offline")
        elif st == "pending" and not self.settings["queue_running"]:
            txt = self.t("st_queue_off")
        else:
            txt = self.t("st_" + st)
        w["status"].configure(text=txt, text_color=DANGER if st == "error" else (SUCCESS if st == "done" else MUTED))

        # الأزرار حسب الحالة
        key = st
        if w.get("btn_state") == key:
            return
        w["btn_state"] = key
        for b in w["btns"].winfo_children():
            b.destroy()
        self.small_btn(w["btns"], self.t("remove"), lambda: self.remove_item(it))
        if st in ("pending", "downloading", "retry", "offline"):
            self.small_btn(w["btns"], self.t("pause"), lambda: self.pause_item(it))
        elif st == "paused":
            self.small_btn(w["btns"], self.t("resume"), lambda: self.resume_item(it), ACCENT)
        elif st == "error":
            self.small_btn(w["btns"], self.t("retry"), lambda: self.resume_item(it), ACCENT)
        elif st == "done":
            self.small_btn(w["btns"], self.t("open"),
                           lambda: open_in_explorer(it.filepath or it.opts.get("folder", "")), SUCCESS)

    def update_queue_meta(self):
        n = len(self.items)
        self.count_label.configure(text=self.t("count", n=n) if n else "")
        if n == 0:
            self.empty_label.pack(pady=60)
        else:
            self.empty_label.pack_forget()

    def update_run_btn(self):
        if self.settings["queue_running"]:
            self.run_btn.configure(text=self.t("pause_all"), fg_color=CARD_2,
                                   text_color=("#111", "#EEE"), hover_color=("#E2E4EC", "#30313C"))
        else:
            self.run_btn.configure(text=self.t("resume_all"), fg_color=ACCENT,
                                   text_color="white", hover_color=ACCENT_HOVER)

    # ───── أحداث الواجهة ─────

    def toggle_language(self):
        self.current_url = self.url_entry.get().strip()
        self.settings["language"] = "en" if self.rtl else "ar"
        self.save_settings()
        self.build_ui()

    def on_theme(self, value):
        mode = "dark" if value == self.t("dark") else "light"
        self.settings["appearance"] = mode
        ctk.set_appearance_mode(mode)
        self.save_settings()

    def on_clip_toggle(self):
        self.settings["clipboard"] = bool(self.clip_var.get())
        self.last_clip = self._read_clipboard()  # تجاهل ما هو موجود حالياً
        self.save_settings()

    def choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.settings["folder"])
        if folder:
            self.settings["folder"] = folder
            self.folder_label.configure(text=shorten(folder, 48))
            self.save_settings()

    def paste_url(self):
        text = self._read_clipboard() or ""
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, text.strip())
        self.fetch_info()

    def show_msg(self, text, color=None):
        self.form_msg.configure(text=text, text_color=color or MUTED)

    # ───── جلب المعلومات ─────

    def fetch_info(self, url=None):
        url = (url or self.url_entry.get()).strip()
        if not re.match(r"^https?://\S+$", url):
            self.show_msg(self.t("invalid"), DANGER)
            return
        self.current_url = url
        self.current_info = None
        self.fetch_btn.configure(state="disabled", text=self.t("fetching"))
        self.show_msg("")
        self.preview.pack_forget()
        threading.Thread(target=self._fetch_thread, args=(url,), daemon=True).start()

    def _fetch_thread(self, url):
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True,
                "logger": _QuietLogger(), "socket_timeout": 20}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                self.ui_events.put(("fetch_error", url, self.t("playlist")))
                return
            thumb = None
            if info.get("thumbnail"):
                try:
                    req = urllib.request.Request(info["thumbnail"], headers={"User-Agent": "Mozilla/5.0"})
                    data = urllib.request.urlopen(req, timeout=10).read()
                    thumb = Image.open(io.BytesIO(data)).convert("RGB")
                except Exception:
                    thumb = None
            self.ui_events.put(("fetched", url, info, thumb))
        except Exception as e:
            self.ui_events.put(("fetch_error", url, self.t("fetch_fail", e=clean_error(e))))

    def on_fetched(self, url, info, thumb):
        if url != self.current_url:
            return
        self.current_info = info
        self.fetch_btn.configure(state="normal", text=self.t("fetch"))
        self.show_msg("")
        self.refresh_form(thumb)

    def refresh_form(self, thumb=None):
        info = self.current_info
        if not info:
            self.quality_map = {self.t("best"): "best", self.t("audio"): "audio"}
            self.quality_menu.configure(values=list(self.quality_map))
            self.quality_menu.set(self.t("best"))
            self.update_sub_options()
            return

        # المعاينة
        if thumb is not None:
            self.thumb_image = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(176, 99))
        if self.thumb_image is not None:
            self.thumb_label.configure(image=self.thumb_image)
        self.pv_title.configure(text=shorten(info.get("title"), 90))
        meta = [info.get("uploader") or info.get("channel") or "",
                f"{self.t('duration')}: {fmt_time(info.get('duration'))}" if info.get("duration") else ""]
        self.pv_meta.configure(text="   •   ".join(m for m in meta if m))
        self.preview.pack(fill="x", padx=18, pady=(0, 16))

        # الجودات
        formats = info.get("formats") or []
        audio_sizes = [f.get("filesize") or f.get("filesize_approx") or 0
                       for f in formats if f.get("vcodec") == "none" and f.get("acodec") not in (None, "none")]
        best_audio = max(audio_sizes) if audio_sizes else 0
        heights = {}
        for f in formats:
            h = f.get("height")
            if not h or f.get("vcodec") in (None, "none"):
                continue
            size = f.get("filesize") or f.get("filesize_approx") or 0
            if f.get("acodec") in (None, "none"):
                size = size + best_audio if size else 0
            heights[h] = max(heights.get(h, 0), size)

        names = {2160: " (4K)", 1440: " (2K)", 1080: " (Full HD)", 720: " (HD)"}
        self.quality_map = {self.t("best"): "best"}
        for h in sorted(heights, reverse=True):
            label = f"{h}p{names.get(h, '')}"
            if heights[h]:
                label += f"   ~{fmt_bytes(heights[h])}"
            self.quality_map[label] = str(h)
        audio_label = self.t("audio") + (f"   ~{fmt_bytes(best_audio)}" if best_audio else "")
        self.quality_map[audio_label] = "audio"
        values = list(self.quality_map)
        self.quality_menu.configure(values=values)
        self.quality_menu.set(values[1] if len(values) > 2 else values[0])
        self.update_sub_options()

    def on_fetch_error(self, url, msg):
        if url != self.current_url:
            return
        self.fetch_btn.configure(state="normal", text=self.t("fetch"))
        self.show_msg(msg, DANGER)

    # ───── الترجمة ─────

    def sub_type(self):
        vals = [self.t("sub_none"), self.t("sub_manual"), self.t("sub_auto")]
        v = self.sub_seg.get()
        return self.sub_keys[vals.index(v)] if v in vals else "none"

    def update_sub_options(self):
        st = self.sub_type()
        if st == "none":
            self.sub_box.pack_forget()
            return
        self.sub_box.pack(fill="x", after=self.sub_seg)
        info = self.current_info or {}
        source = info.get("subtitles" if st == "manual" else "automatic_captions") or {}
        langs = {}
        for code, tracks in source.items():
            if code == "live_chat":
                continue
            name = (tracks[0].get("name") if tracks else None) or code
            langs[f"{name} ({code})"] = code
        # العربية والإنجليزية أولاً
        def order(item):
            code = item[1]
            base = code.split("-")[0]
            return (0 if base == "ar" else 1 if base == "en" else 2, item[0].lower())
        self.lang_map = dict(sorted(langs.items(), key=order))
        if self.lang_map:
            self.lang_menu.configure(values=list(self.lang_map), state="normal")
            self.lang_menu.set(next(iter(self.lang_map)))
        else:
            self.lang_menu.configure(values=[self.t("no_subs")], state="disabled")
            self.lang_menu.set(self.t("no_subs") if self.current_info else "—")
        self.update_sub_state()

    def update_sub_state(self):
        # مع "صوت فقط" لا يمكن دمج الترجمة داخل الملف
        q = self.quality_map.get(self.quality_menu.get(), "best")
        self.mode_seg.configure(state="disabled" if q == "audio" else "normal")

    # ───── إضافة للقائمة ─────

    def collect_opts(self):
        opts = {
            "quality": self.quality_map.get(self.quality_menu.get(), "best"),
            "sub_type": self.sub_type(),
            "sub_lang": None,
            "sub_fmt": self.fmt_menu.get().lower(),
            "sub_mode": "file",
            "folder": self.settings["folder"],
        }
        if opts["sub_type"] != "none":
            opts["sub_lang"] = getattr(self, "lang_map", {}).get(self.lang_menu.get())
            if not opts["sub_lang"]:
                opts["sub_type"] = "none"
            mode_vals = [self.t("mode_file"), self.t("mode_embed"), self.t("mode_both")]
            m = self.mode_seg.get()
            opts["sub_mode"] = self.mode_keys[mode_vals.index(m)] if m in mode_vals else "file"
        return opts

    def add_current(self):
        url = self.url_entry.get().strip()
        if not re.match(r"^https?://\S+$", url):
            self.show_msg(self.t("invalid"), DANGER)
            return
        title = self.current_info.get("title") if (self.current_info and url == self.current_url) else url
        self.add_item(url, title, self.collect_opts())
        self.show_msg(self.t("added"), SUCCESS)

    def add_item(self, url, title, opts):
        it = Item(url, title, opts)
        self.items.append(it)
        self.create_item_card(it)
        self.update_queue_meta()
        self.save_queue()
        self.wake.set()

    def pause_item(self, it):
        if it.status in ("downloading", "retry", "offline", "processing"):
            it.stop_reason = "pause"
        else:
            it.status = "paused"
            self.update_item_card(it)
            self.save_queue()

    def resume_item(self, it):
        it.status = "pending"
        it.error = ""
        it.stop_reason = None
        self.update_item_card(it)
        self.save_queue()
        self.wake.set()

    def remove_item(self, it):
        if it.status in ("downloading", "retry", "offline", "processing"):
            it.stop_reason = "remove"
        if it in self.items:
            self.items.remove(it)
        if it.widgets.get("card"):
            it.widgets["card"].destroy()
        it.widgets = {}
        self.update_queue_meta()
        self.save_queue()

    def clear_done(self):
        for it in [i for i in self.items if i.status == "done"]:
            self.remove_item(it)

    def toggle_queue(self):
        self.settings["queue_running"] = not self.settings["queue_running"]
        self.save_settings()
        self.update_run_btn()
        for it in self.items:
            if it.status == "pending":
                self.update_item_card(it)
        self.wake.set()

    # ───── عامل التحميل (خيط منفصل) ─────

    def worker_loop(self):
        while True:
            self.wake.wait(2)
            self.wake.clear()
            while self.settings["queue_running"]:
                nxt = next((i for i in list(self.items) if i.status == "pending"), None)
                if not nxt:
                    break
                self.download(nxt)

    def notify(self, it):
        self.ui_events.put(("item", it))

    def build_ydl_opts(self, it):
        o = it.opts
        folder = o.get("folder") or DEFAULT_FOLDER
        os.makedirs(folder, exist_ok=True)
        q = o.get("quality", "best")
        ff = self.ffmpeg
        pps = []

        opts = {
            "outtmpl": os.path.join(folder, "%(title).150B [%(id)s].%(ext)s"),
            "noplaylist": True,
            "continuedl": True,          # يكمل الملف الجزئي .part
            "retries": 10,
            "fragment_retries": 10,
            "socket_timeout": 30,
            "windowsfilenames": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "logger": _QuietLogger(),
            "progress_hooks": [lambda d: self._progress_hook(it, d)],
            "postprocessor_hooks": [lambda d: self._pp_hook(it, d)],
            "post_hooks": [lambda path: setattr(it, "filepath", path)],
        }
        if ff:
            opts["ffmpeg_location"] = ff

        if q == "audio":
            if ff:
                opts["format"] = "bestaudio/best"
                pps.append({"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"})
            else:
                opts["format"] = "bestaudio[ext=m4a]/bestaudio/best"
        elif ff:
            h = "" if q == "best" else f"[height<={q}]"
            opts["format"] = f"bv*{h}[ext=mp4]+ba[ext=m4a]/bv*{h}+ba/b{h}/b"
            opts["merge_output_format"] = "mp4"
        else:
            h = "" if q == "best" else f"[height<={q}]"
            opts["format"] = f"b{h}[acodec!=none][vcodec!=none]/b"

        st = o.get("sub_type", "none")
        if st != "none" and o.get("sub_lang"):
            fmt = o.get("sub_fmt") or "srt"
            opts["writesubtitles"] = st == "manual"
            opts["writeautomaticsub"] = st == "auto"
            opts["subtitleslangs"] = [o["sub_lang"]]
            opts["subtitlesformat"] = f"{fmt}/best"
            if ff:
                pps.append({"key": "FFmpegSubtitlesConvertor", "format": fmt, "when": "before_dl"})
                mode = o.get("sub_mode", "file")
                if q != "audio" and mode in ("embed", "both"):
                    pps.append({"key": "FFmpegEmbedSubtitle", "already_have_subtitle": mode == "both"})
        if pps:
            opts["postprocessors"] = pps
        return opts

    def _progress_hook(self, it, d):
        if it.stop_reason:
            raise StopRequested()
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            done = d.get("downloaded_bytes") or 0
            it.progress = (done / total) if total else it.progress
            it.speed = d.get("speed")
            it.eta = d.get("eta")
            if it.status != "downloading":
                it.status = "downloading"
            self.notify(it)
        elif d.get("status") == "finished":
            it.progress = 1.0
            self.notify(it)

    def _pp_hook(self, it, d):
        if d.get("status") == "started" and it.status != "processing":
            it.status = "processing"
            self.notify(it)

    def _wait(self, it, seconds, status):
        """ينتظر مع إمكانية الإيقاف. يعيد False إذا طلب المستخدم الإيقاف."""
        it.status = status
        end = time.time() + seconds
        while time.time() < end:
            if it.stop_reason:
                return False
            it.retry_in = int(end - time.time()) + 1
            self.notify(it)
            time.sleep(0.5)
        return True

    def download(self, it):
        it.status = "downloading"
        it.error = ""
        it.progress = 0.0
        self.notify(it)
        failures = 0
        while True:
            try:
                with yt_dlp.YoutubeDL(self.build_ydl_opts(it)) as ydl:
                    code = ydl.download([it.url])
                if code:
                    raise DownloadError("download failed")
                it.status = "done"
                it.progress = 1.0
                break
            except DownloadCancelled:
                break
            except Exception as e:
                if it.stop_reason:
                    break
                msg = clean_error(e)
                # انقطاع الإنترنت: انتظر حتى يعود ثم أكمل من حيث توقف
                if not is_online():
                    while not is_online():
                        if not self._wait(it, 5, "offline"):
                            break
                    if it.stop_reason:
                        break
                    continue
                if looks_like_network_error(msg) and failures < 8:
                    failures += 1
                    if not self._wait(it, min(5 * failures, 30), "retry"):
                        break
                    continue
                it.status = "error"
                it.error = msg
                break

        if it.stop_reason == "pause":
            it.status = "paused"
        it.stop_reason = None
        it.speed = it.eta = None
        self.notify(it)
        self.queue_dirty = True

    # ───── حلقة تحديث الواجهة ─────

    def poll_events(self):
        try:
            for _ in range(300):
                ev = self.ui_events.get_nowait()
                kind = ev[0]
                if kind == "item":
                    self.dirty.add(ev[1])
                elif kind == "fetched":
                    self.on_fetched(*ev[1:])
                elif kind == "fetch_error":
                    self.on_fetch_error(*ev[1:])
        except queue.Empty:
            pass
        for it in self.dirty:
            if it in self.items:
                self.update_item_card(it)
        self.dirty.clear()
        if self.queue_dirty:
            self.queue_dirty = False
            self.save_queue()
        self.after(150, self.poll_events)

    # ───── مراقبة الحافظة ─────

    def _load_extractors(self):
        try:
            self.extractors = [ie for ie in yt_dlp.extractor.gen_extractor_classes()
                               if ie.ie_key() != "Generic"]
        except Exception:
            self.extractors = []

    def _read_clipboard(self):
        try:
            return self.clipboard_get()
        except (TclError, Exception):
            return None

    def is_supported(self, url):
        if not self.extractors:
            return bool(re.search(r"(youtube\.com|youtu\.be)/", url))
        return any(ie.suitable(url) for ie in self.extractors)

    def poll_clipboard(self):
        try:
            if self.settings["clipboard"]:
                text = self._read_clipboard()
                if self.last_clip is None:
                    self.last_clip = text  # لا نقترح ما كان منسوخاً قبل فتح البرنامج
                elif text and text != self.last_clip:
                    self.last_clip = text
                    url = text.strip()
                    if re.match(r"^https?://\S+$", url) and len(url) < 500 and self.is_supported(url) \
                            and url != self.url_entry.get().strip() \
                            and not any(i.url == url and i.status != "done" for i in self.items):
                        self.show_toast(url)
        finally:
            self.after(1000, self.poll_clipboard)

    def show_toast(self, url):
        if self.toast is not None:
            self.toast.destroy()
        toast = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14, border_width=2, border_color=ACCENT)
        self.toast = toast
        ctk.CTkLabel(toast, text="📋  " + self.t("detected"), font=self.font(13, "bold"),
                     anchor=self.anchor).pack(fill="x", padx=14, pady=(10, 0))
        ctk.CTkLabel(toast, text=shorten(url, 60), font=self.font(11), text_color=MUTED,
                     anchor="w").pack(fill="x", padx=14)
        row = ctk.CTkFrame(toast, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=10)

        def close():
            if self.toast is toast:
                self.toast = None
            toast.destroy()

        def details():
            close()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)
            self.fetch_info()

        def quick():
            close()
            q = self.settings.get("quick_quality", "1080")
            self.add_item(url, url, {"quality": q, "sub_type": "none", "sub_lang": None,
                                     "sub_fmt": "srt", "sub_mode": "file", "folder": self.settings["folder"]})
            threading.Thread(target=self._fill_title, args=(url,), daemon=True).start()

        for text, cmd, color in ((self.t("quick"), quick, ACCENT), (self.t("details"), details, None),
                                 (self.t("ignore"), close, None)):
            ctk.CTkButton(row, text=text, height=30, width=96, corner_radius=8, font=self.font(12),
                          fg_color=color or CARD_2, hover_color=ACCENT_HOVER if color else ("#E2E4EC", "#30313C"),
                          text_color="white" if color else ("#111", "#EEE"),
                          command=cmd).pack(side=self.side, padx=4)
        toast.place(relx=0.02 if self.rtl else 0.98, rely=0.97, anchor="sw" if self.rtl else "se")
        toast.lift()
        self.after(15000, lambda: toast.winfo_exists() and close())

    def _fill_title(self, url):
        """يجلب عنوان الفيديو للتحميل السريع ليظهر بشكل أجمل في القائمة."""
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True, "noplaylist": True,
                                   "logger": _QuietLogger(), "extract_flat": True}) as ydl:
                info = ydl.extract_info(url, download=False)
            title = info.get("title")
            if title:
                for it in self.items:
                    if it.url == url and it.title == url:
                        it.title = title
                        self.after(0, lambda i=it: i.widgets.get("title") and
                                   i.widgets["title"].configure(text=shorten(title, 58)))
                self.queue_dirty = True
        except Exception:
            pass

    # ───── الإغلاق ─────

    def on_close(self):
        self.save_queue()
        self.save_settings()
        self.destroy()
        os._exit(0)  # ينهي خيوط التحميل؛ الملفات الجزئية تبقى ويكمل منها لاحقاً


if __name__ == "__main__":
    os.makedirs(CONFIG_DIR, exist_ok=True)
    app = VidDropApp()
    app.mainloop()
