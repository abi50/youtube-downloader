import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from pathlib import Path
import sys
import os
import logging

import truststore
# Trust the OS certificate store (Windows) in addition to the bundled CA
# bundle, the same way browsers do. This lets legitimate local software
# (antivirus/firewall HTTPS scanning) that injects a trusted root
# certificate work, without disabling certificate verification.
truststore.inject_into_ssl()

from yt_dlp import YoutubeDL

# ================== Logic ==================

def get_app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

LOG_PATH = os.path.join(get_app_dir(), "youtube_downloader.log")

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
_logger = logging.getLogger("yt_dlp")


class YDLLogger:
    """Routes yt-dlp's verbose/debug output into youtube_downloader.log."""

    def debug(self, msg):
        if msg.startswith("[debug] "):
            _logger.debug(msg)
        else:
            self.info(msg)

    def info(self, msg):
        _logger.info(msg)

    def warning(self, msg):
        _logger.warning(msg)

    def error(self, msg):
        _logger.error(msg)


_UNAVAILABLE_MARKERS = (
    "video is unavailable",
    "private video",
    "video has been removed",
    "account associated with this video has been terminated",
    "this video is no longer available",
)


_PLAYER_RESPONSE_MARKERS = (
    "failed to extract any player response",
)


_CERT_ERROR_MARKERS = (
    "certificate_verify_failed",
    "certificate verify failed",
)


def is_certificate_error(error):
    return any(marker in str(error).lower() for marker in _CERT_ERROR_MARKERS)


def friendly_error_message(error):
    text = str(error).lower()
    if any(marker in text for marker in _UNAVAILABLE_MARKERS):
        return "הסרטון אינו זמין (הוסר, הוגדר כפרטי, או אינו קיים יותר ביוטיוב)."
    if any(marker in text for marker in _PLAYER_RESPONSE_MARKERS):
        return (
            "יוטיוב חסם או דחה את הבקשה להורדת הסרטון הזה (לא בהכרח שהסרטון אינו זמין).\n"
            "נסה שוב בעוד כמה דקות. אם זה ממשיך לקרות, ייתכן שהסרטון דורש התחברות "
            "(מוגבל לגיל, לחברי ערוץ בלבד, או מוגבל לאזור מסוים)."
        )
    if is_certificate_error(error):
        return (
            "שגיאת אימות אבטחה (SSL) בחיבור לשרת של יוטיוב.\n"
            "ייתכן שתוכנת אנטי-וירוס/חומת אש על המחשב חוסמת או בודקת את החיבור המוצפן, "
            "או שיש בעיית רשת/תאריך שעה שגוי במחשב.\n"
            "בדוק את הגדרות האנטי-וירוס/החומת אש ונסה שוב."
        )
    return str(error)


def get_ffmpeg_path():
    if getattr(sys, "frozen", False):
        # running as EXE
        return os.path.join(sys._MEIPASS, "ffmpeg")
    else:
        # running as .py
        return "ffmpeg"

def get_deno_path():
    if getattr(sys, "frozen", False):
        # running as EXE
        return os.path.join(sys._MEIPASS, "deno", "deno.exe")
    else:
        # running as .py
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "deno", "deno.exe")

def download_video():
    url = url_entry.get().strip()
    quality = quality_var.get()

    if not url:
        messagebox.showerror("שגיאה", "נא להכניס קישור")
        return

    output_dir = Path("downloads")
    output_dir.mkdir(exist_ok=True)

    ydl_opts = {
        "outtmpl": str(output_dir / '%(title)s.%(ext)s'),
        "quiet": True,
        "verbose": True,
        "logger": YDLLogger(),
        "retries": 5,
        "fragment_retries": 5,
    }
    ydl_opts["ffmpeg_location"] = get_ffmpeg_path()
    ydl_opts["js_runtimes"] = {"deno": {"path": get_deno_path()}}

    if quality == "720p":
        ydl_opts["format"] = "bestvideo[height<=720]+bestaudio/best[height<=720]"
        ydl_opts["merge_output_format"] = "mp4"
    elif quality == "480p":
        ydl_opts["format"] = "bestvideo[height<=480]+bestaudio/best[height<=480]"
        ydl_opts["merge_output_format"] = "mp4"
    elif quality == "אודיו בלבד (mp3)":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }]
        })
    else:
        ydl_opts["format"] = "bestvideo+bestaudio/best"
        ydl_opts["merge_output_format"] = "mp4"

    try:
        status_label.config(text="מוריד...")
        root.update()

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        status_label.config(text="ההורדה הושלמה ✅")
        messagebox.showinfo("סיום", "הקובץ ירד בהצלחה")
    except Exception as e:
        _logger.exception("Download failed")
        status_label.config(text="שגיאה")
        messagebox.showerror("שגיאה", friendly_error_message(e))


def show_about():
    messagebox.showinfo(
        "About",
        "YouTube Downloader\n\n"
        "Version: 1.0.3\n"
        "Developed by Abigail Berk\n\n"
        "Desktop application for personal use.\n"
        "No data collection."
    )

def paste_clipboard():
    try:
       text= root.clipboard_get()
       url_entry.insert(tk.INSERT, text)
    except tk.TclError:
        pass

# ================== GUI ==================

root = tk.Tk()
root.title("YouTube Downloader")
root.geometry("420x320")
root.resizable(False, False)

# ---- Main content frame ----
content = tk.Frame(root, padx=20, pady=15)
content.pack(fill="both", expand=True)

# About button (top-right)
tk.Button(
    content,
    text="About",
    command=show_about,
    font=("Segoe UI", 9),
    relief="flat"
).pack(anchor="e")

# URL input
tk.Label(
    content,
    text="קישור לסרטון:",
    font=("Segoe UI", 11)
).pack(pady=(10, 5))

url_entry = tk.Entry(content, width=50)
url_entry.pack()
url_entry.focus_set()
url_entry.bind("<Control-v>", paste_clipboard)

# Quality selector
quality_var = tk.StringVar(value="איכות מקסימלית")

ttk.Label(
    content,
    text="בחר איכות:",
    font=("Segoe UI", 10)
).pack(pady=(10, 5))

quality_box = ttk.Combobox(
    content,
    textvariable=quality_var,
    values=[
        "איכות מקסימלית",
        "720p",
        "480p",
        "אודיו בלבד (mp3)"
    ],
    state="readonly"
)
quality_box.pack()

# Download button
tk.Button(
    content,
    text="⬇ הורד",
    command=download_video,
    bg="#2D8CFF",
    fg="white",
    font=("Segoe UI", 11, "bold"),
    relief="flat",
    width=18,
    cursor="hand2"
).pack(pady=15)

# Status
status_label = tk.Label(
    content,
    text="",
    font=("Segoe UI", 10)
)
status_label.pack()

footer = tk.Label(
    root,
    text="Developed by Abigail Berk © 2026",
    font=("Segoe UI", 8),
    fg="#AC1212"
)
footer.pack(side="bottom", pady=6)

root.mainloop()
