import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
from pathlib import Path
from yt_dlp import YoutubeDL
import sys
import os

# ================== Logic ==================

def get_ffmpeg_path():
    if getattr(sys, "frozen", False):        
        # running as EXE
        return os.path.join(sys._MEIPASS, "ffmpeg")
    else:
        # running as .py
        return "ffmpeg"

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
        "quiet": True
    }
    ydl_opts["ffmpeg_location"] = get_ffmpeg_path()

    if quality == "720p":
        ydl_opts["format"] = "best[height<=720]"
    elif quality == "480p":
        ydl_opts["format"] = "best[height<=480]"
    elif quality == "אודיו בלבד (mp3)":
        ydl_opts.update({
            "format": "bestaudio",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
            }]
        })
    else:
        ydl_opts["format"] = "best"

    try:
        status_label.config(text="מוריד...")
        root.update()

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        status_label.config(text="ההורדה הושלמה ✅")
        messagebox.showinfo("סיום", "הקובץ ירד בהצלחה")
    except Exception as e:
        status_label.config(text="שגיאה")
        messagebox.showerror("שגיאה", str(e))


def show_about():
    messagebox.showinfo(
        "About",
        "YouTube Downloader\n\n"
        "Version: 1.0.0\n"
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
