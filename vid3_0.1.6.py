import os
import cv2
import pygame
import threading
import subprocess
import shutil
from datetime import datetime
from tkinter import *
from tkinter import filedialog, messagebox, colorchooser
from tkinter.ttk import Progressbar
import customtkinter as ctk
from PIL import Image, ImageTk
import numpy as np

# pip install customtkinter opencv-python pygame pillow

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

ASCII_CHARS = "@%#*+=-:. "[::-1]

class ASCIIConverterApp:
    def __init__(self):
        pygame.init()
        self.root = ctk.CTk()
        self.root.title("ASCII Video Converter")
        self.root.geometry("1600x1000")

        self.first_frame = None

        # Переменные
        self.video_path = StringVar()
        self.char_width = ctk.IntVar(value=250)
        self.height_ratio = ctk.DoubleVar(value=0.55)
        self.invert = ctk.BooleanVar(value=False)
        self.transparent = ctk.BooleanVar(value=False)
        self.threshold = ctk.IntVar(value=150)
        self.text_color = "#bdf282"
        self.bg_color_hex = "#1e1e1e"
        self.random_colors = ctk.BooleanVar(value=False)
        self.save_txt = ctk.BooleanVar(value=True)
        self.save_png = ctk.BooleanVar(value=True)
        self.save_video = ctk.BooleanVar(value=False)
        self.video_quality = ctk.StringVar(value="Высокое")

        # Камера
        self.brightness = ctk.IntVar(value=0)
        self.contrast = ctk.DoubleVar(value=1.0)
        self.gamma = ctk.DoubleVar(value=1.0)

        self.setup_ui()
        self.bind_changes()

    def setup_ui(self):
        # Логотип
        ctk.CTkLabel(self.root, text="""
 ___ ___ _______ _____ ______
| | |_ _| \|__ |
| | |_| |_| -- |__ |
 \_____/|_______|_____/|______|
                              
        """, font=("Courier New", 20, "bold"), text_color="#bdf282").pack(anchor="w", padx=40, pady=30)

        main = ctk.CTkFrame(self.root)
        main.pack(fill=BOTH, expand=True, padx=40, pady=10)

        # Левая панель с прокруткой
        left_scroll = ctk.CTkScrollableFrame(main, width=500, corner_radius=15)
        left_scroll.pack(side=LEFT, fill=Y, padx=(0,40), pady=20)

        ctk.CTkLabel(left_scroll, text="Настройки", font=("Segoe UI", 22, "bold"), text_color="#bdf282").pack(pady=20, anchor="w", padx=30)

        # Видео
        video_frame = ctk.CTkFrame(left_scroll)
        video_frame.pack(fill=X, pady=10, padx=30)
        ctk.CTkEntry(video_frame, textvariable=self.video_path, state="readonly", placeholder_text="Выберите видео...", height=40).pack(side=LEFT, fill=X, expand=True, padx=(10,5))
        ctk.CTkButton(video_frame, text="Обзор...", command=self.browse_video, height=40, corner_radius=10).pack(side=RIGHT, padx=(5,10))

        # Слайдеры
        def slider(text, var, from_, to_, step=None):
            ctk.CTkLabel(left_scroll, text=text, font=("Segoe UI", 12)).pack(anchor="w", padx=40, pady=(20,5))
            if step:
                ctk.CTkSlider(left_scroll, from_=from_, to=to_, variable=var, number_of_steps=int((to_-from_)/step)).pack(fill=X, padx=40)
            else:
                ctk.CTkSlider(left_scroll, from_=from_, to=to_, variable=var).pack(fill=X, padx=40)

        slider("Ширина (символов)", self.char_width, 100, 400)
        slider("Соотношение сторон", self.height_ratio, 0.3, 1.0, 0.05)

        # Камера
        ctk.CTkLabel(left_scroll, text="Яркость / Контраст / Гамма", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        slider("Яркость", self.brightness, -100, 100)
        slider("Контраст", self.contrast, 0.1, 3.0, 0.1)
        slider("Гамма", self.gamma, 0.1, 3.0, 0.1)

        # Стиль
        ctk.CTkLabel(left_scroll, text="Стиль", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        ctk.CTkCheckBox(left_scroll, text="Инвертировать", variable=self.invert).pack(anchor="w", padx=50)
        ctk.CTkCheckBox(left_scroll, text="Прозрачный фон", variable=self.transparent).pack(anchor="w", padx=50)
        ctk.CTkCheckBox(left_scroll, text="Случайные цвета", variable=self.random_colors).pack(anchor="w", padx=50)

        # Цвета
        ctk.CTkLabel(left_scroll, text="Цвет текста", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        ctk.CTkButton(left_scroll, text="Выбрать цвет", command=self.choose_text_color, width=200).pack(padx=50, pady=5)
        self.text_color_btn = ctk.CTkLabel(left_scroll, text="#bdf282", width=100, height=30, corner_radius=10, fg_color="#bdf282")
        self.text_color_btn.pack(padx=50, pady=5)

        ctk.CTkLabel(left_scroll, text="Фон", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        ctk.CTkButton(left_scroll, text="Выбрать фон", command=self.choose_bg_color, width=200).pack(padx=50, pady=5)
        self.bg_color_btn = ctk.CTkLabel(left_scroll, text="#1e1e1e", width=100, height=30, corner_radius=10, fg_color="#1e1e1e")
        self.bg_color_btn.pack(padx=50, pady=5)

        # Качество видео
        ctk.CTkLabel(left_scroll, text="Качество MP4", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        ctk.CTkComboBox(left_scroll, values=["Низкое", "Среднее", "Высокое", "Без потерь"], variable=self.video_quality).pack(padx=50, pady=5)

        # Сохранение
        ctk.CTkLabel(left_scroll, text="Сохранить как", font=("Segoe UI", 16, "bold"), text_color="#bdf282").pack(anchor="w", padx=30, pady=(20,10))
        ctk.CTkCheckBox(left_scroll, text="TXT файлы", variable=self.save_txt).pack(anchor="w", padx=50)
        ctk.CTkCheckBox(left_scroll, text="PNG кадры", variable=self.save_png).pack(anchor="w", padx=50)
        ctk.CTkCheckBox(left_scroll, text="MP4 видео", variable=self.save_video).pack(anchor="w", padx=50)

        ctk.CTkButton(left_scroll, text="ЗАПУСТИТЬ КОНВЕРТАЦИЮ", command=self.start_conversion,
                      font=("Segoe UI", 18, "bold"), height=50, corner_radius=15).pack(fill=X, padx=80, pady=40)

        # Правая панель
        right = ctk.CTkFrame(main, fg_color="#1a1a1a")
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=20, pady=20)

        self.preview_canvas = Canvas(right, bg="#1a1a1a", highlightthickness=0)
        self.preview_canvas.pack(fill=BOTH, expand=True)

        self.progress = Progressbar(self.root, length=1000, mode="determinate")
        self.progress.pack(fill=X, padx=200, pady=20)

        self.status = ctk.CTkLabel(self.root, text="Готов к работе", font=("Segoe UI", 12))
        self.status.pack(pady=10)

    def choose_text_color(self):
        color = colorchooser.askcolor(title="Цвет текста", initialcolor=self.text_color)[1]
        if color:
            self.text_color = color
            self.text_color_btn.configure(fg_color=color, text=color.upper())

    def choose_bg_color(self):
        color = colorchooser.askcolor(title="Цвет фона", initialcolor=self.bg_color_hex)[1]
        if color:
            self.bg_color_hex = color
            self.bg_color_btn.configure(fg_color=color, text=color.upper())

    def bind_changes(self):
        for var in [self.invert, self.transparent, self.threshold, self.char_width, self.height_ratio,
                    self.brightness, self.contrast, self.gamma]:
            var.trace_add("write", lambda *args: self.root.after_idle(self.update_preview))

    def browse_video(self):
        path = filedialog.askopenfilename(filetypes=[("Видео", "*.mp4 *.avi *.mov *.mkv *.webm")])
        if path:
            self.video_path.set(path)
            self.load_first_frame()

    def load_first_frame(self):
        path = self.video_path.get()
        if not path: return
        cap = cv2.VideoCapture(path)
        ret, frame = cap.read()
        cap.release()
        if ret:
            self.first_frame = frame
            self.update_preview()

    def apply_camera_settings(self, gray):
        img = gray.astype(np.float32)
        img = img * self.contrast.get() + self.brightness.get()
        img = np.clip(img, 0, 255)
        img = np.power(img / 255.0, self.gamma.get()) * 255.0
        return np.clip(img, 0, 255).astype(np.uint8)

    def update_preview(self):
        if self.first_frame is None:
            return

        frame = self.first_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = self.apply_camera_settings(gray)
        if self.invert.get():
            gray = 255 - gray

        chars_w = self.char_width.get()
        chars_h = int(chars_w * self.height_ratio.get())
        if chars_h < 20: chars_h = 20

        resized = cv2.resize(gray, (chars_w, chars_h), interpolation=cv2.INTER_AREA)

        canvas_w = self.preview_canvas.winfo_width()
        canvas_h = self.preview_canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            canvas_w, canvas_h = 1200, 800

        char_w = canvas_w // chars_w
        char_h = canvas_h // chars_h
        char_size = min(char_w, char_h)
        if char_size < 4: char_size = 4

        surf = pygame.Surface((chars_w * char_size, chars_h * char_size))
        surf.fill(self.bg_color_hex)

        font = pygame.font.SysFont("Courier New", char_size, bold=True)
        color = self.text_color if not self.random_colors.get() else "#ffffff"

        for y in range(chars_h):
            for x in range(chars_w):
                p = resized[y, x]
                if self.transparent.get() and p > self.threshold.get():
                    char = " "
                else:
                    char = ASCII_CHARS[min(len(ASCII_CHARS)-1, p // 32)]
                txt = font.render(char, True, color)
                surf.blit(txt, (x * char_size, y * char_size))

        data = pygame.image.tostring(surf, 'RGB')
        image = Image.frombytes('RGB', surf.get_size(), data)
        image_tk = ImageTk.PhotoImage(image)

        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(canvas_w//2, canvas_h//2, image=image_tk, anchor="center")
        self.preview_image = image_tk

    def start_conversion(self):
        if not self.video_path.get():
            messagebox.showerror("Ошибка", "Выберите видео!")
            return
        self.progress['value'] = 0
        self.status.configure(text="Конвертация...")
        threading.Thread(target=self.convert, daemon=True).start()

    def convert(self):
        path = self.video_path.get()
        cap = cv2.VideoCapture(path)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        w, h = int(cap.get(3)), int(cap.get(4))

        out_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ASCII_Videos")
        os.makedirs(out_dir, exist_ok=True)
        folder = os.path.join(out_dir, datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
        os.makedirs(folder, exist_ok=True)
        frames_dir = os.path.join(folder, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        temp_dir = os.path.join(folder, "temp") if self.save_video.get() else None
        if temp_dir:
            os.makedirs(temp_dir, exist_ok=True)

        chars_w = self.char_width.get()
        chars_h = int(chars_w * self.height_ratio.get())
        if chars_h < 20: chars_h = 20

        font = pygame.font.SysFont("Courier New", max(12, w // chars_w * 2), bold=True)

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = self.apply_camera_settings(gray)
            if self.invert.get(): gray = 255 - gray

            resized = cv2.resize(gray, (chars_w, chars_h))

            surf = pygame.Surface((w, h))
            surf.fill(self.bg_color_hex)
            color = self.text_color if not self.random_colors.get() else "#ffffff"

            total_text_w = chars_w * font.get_height()
            total_text_h = chars_h * font.get_height()
            start_x = (w - total_text_w) // 2
            start_y = (h - total_text_h) // 2

            y = start_y
            for row in resized:
                x = start_x
                for p in row:
                    if self.transparent.get() and p > self.threshold.get():
                        char = " "
                    else:
                        char = ASCII_CHARS[min(len(ASCII_CHARS)-1, p // 32)]
                    txt = font.render(char, True, color)
                    surf.blit(txt, (x, y))
                    x += font.get_height()
                y += font.get_height()

            if self.save_txt.get():
                text = "\n".join("".join(" " if self.transparent.get() and p > self.threshold.get() else ASCII_CHARS[p//32] for p in row) for row in resized)
                open(os.path.join(frames_dir, f"frame_{frame_idx:06d}.txt"), "w", encoding="utf-8").write(text)

            if self.save_png.get():
                pygame.image.save(surf, os.path.join(frames_dir, f"frame_{frame_idx:06d}.png"))
            if temp_dir:
                pygame.image.save(surf, os.path.join(temp_dir, f"frame_{frame_idx:06d}.png"))

            frame_idx += 1
            self.root.after(0, lambda: self.progress.config(value=frame_idx / total * 100 if total else 0))

        cap.release()

        if temp_dir and os.listdir(temp_dir):
            video_path = os.path.join(folder, "ascii_video.mp4")

            quality = self.video_quality.get()
            if quality == "Низкое":
                extra = ["-crf", "28"]
            elif quality == "Среднее":
                extra = ["-crf", "23"]
            elif quality == "Высокое":
                extra = ["-crf", "18"]
            else:
                extra = ["-qp", "0", "-preset", "ultrafast"]

            subprocess.run([
                "ffmpeg", "-y", "-framerate", str(fps),
                "-i", os.path.join(temp_dir, "frame_%06d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p"
            ] + extra + [
                "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",
                video_path
            ], check=False)
            shutil.rmtree(temp_dir)

        self.root.after(0, lambda: (
            self.progress.config(value=100),
            self.status.configure(text=f"ГОТОВО! Папка: {folder}"),
            messagebox.showinfo("Успех!", f"Сохранено в:\n{folder}")
        ))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    ASCIIConverterApp().run()