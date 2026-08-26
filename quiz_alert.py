#!/usr/bin/env python3
"""9급 전기직 기출 알림 퀴즈. 문제를 보고 풀이를 확인해야 창이 닫힌다."""

from __future__ import annotations

import ctypes
import hashlib
import io
import json
import math
import random
import struct
import sys
import time
import wave

try:
    import winsound
except ImportError:
    winsound = None

import tkinter as tk
from tkinter import font as tkfont

from app_paths import progress_path, resolve_media_path, resolve_questions_path
from mini_tips import MINI_TIPS
from pixel_art import PixelSurf, render_visual

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None  # type: ignore[assignment, misc]
    ImageTk = None  # type: ignore[assignment, misc]

MUTEX_NAME = "Local\\QuizAlertSingleInstance"
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
ERROR_ALREADY_EXISTS = 183
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000

BG = "#0b0d12"
CARD = "#161b26"
CARD_LINE = "#2a3348"
TEXT = "#f4f6fb"
MUTED = "#9aa3b8"
ACCENT = "#6c8cff"
WRONG = "#ff5c7a"
OK = "#3dd68c"
BTN = "#222a3a"
BTN_HOVER = "#2e3850"
TIP_ROTATE_MS = 20_000
TIP_ACCENT = "#f8d030"


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def ensure_single_instance() -> bool:
    if sys.platform != "win32":
        return True
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle:
        return True
    if ctypes.windll.kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        return False
    return True


def force_foreground(hwnd: int) -> None:
    if sys.platform != "win32" or not hwnd:
        return
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    try:
        user32.AllowSetForegroundWindow(-1)
    except Exception:
        pass
    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(fg, None)
    cur_thread = kernel32.GetCurrentThreadId()
    if fg_thread and fg_thread != cur_thread:
        user32.AttachThreadInput(cur_thread, fg_thread, True)
    user32.ShowWindow(hwnd, 9)
    user32.SetWindowPos(
        hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW
    )
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SetActiveWindow(hwnd)
    user32.SetFocus(hwnd)
    if fg_thread and fg_thread != cur_thread:
        user32.AttachThreadInput(cur_thread, fg_thread, False)


def beep_alert() -> None:
    if winsound is None:
        return
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


def beep_type() -> None:
    """부드러운 타이핑 클릭음 (짧은 감쇠 사인파)."""
    if winsound is None:
        return
    try:
        winsound.PlaySound(
            _soft_type_wav(),
            winsound.SND_MEMORY | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
        )
    except Exception:
        pass


def _soft_type_wav() -> bytes:
    if not hasattr(_soft_type_wav, "cache"):
        rate = 22050
        duration = 0.028
        freq = 720.0 + random.uniform(-35, 35)
        samples = int(rate * duration)
        frames = bytearray()
        for i in range(samples):
            t = i / rate
            env = math.exp(-t * 95)
            sample = int(6200 * env * math.sin(2 * math.pi * freq * t))
            frames += struct.pack("<h", max(-32767, min(32767, sample)))
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(frames)
        _soft_type_wav.cache = buf.getvalue()  # type: ignore[attr-defined]
    return _soft_type_wav.cache  # type: ignore[attr-defined]


def set_window_no_activate(hwnd: int) -> None:
    """클릭해도 다른 창/탭 포커스를 빼앗지 않게 한다."""
    if sys.platform != "win32" or not hwnd:
        return
    try:
        user32 = ctypes.windll.user32
        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE)
    except Exception:
        pass


def question_key(item: dict) -> str:
    return str(item.get("q", "")).strip()


def dedupe_questions(questions: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique: list[dict] = []
    for item in questions:
        key = question_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def bank_signature(questions: list[dict]) -> str:
    blob = "\n".join(sorted(question_key(q) for q in questions))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


def load_question_pool(questions: list[dict]) -> list[dict]:
    """남은 문제 풀을 복원한다. 전부 소진하기 전까지 같은 문제는 다시 나오지 않는다."""
    path = progress_path()
    key_to_item = {question_key(q): q for q in questions}
    sig = bank_signature(questions)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("bank_sig") == sig:
                saved = data.get("remaining") or []
                pool = [key_to_item[k] for k in saved if k in key_to_item]
                if pool:
                    random.shuffle(pool)
                    save_question_pool(pool, questions)
                    return pool
        except Exception:
            pass
    pool = list(questions)
    random.shuffle(pool)
    save_question_pool(pool, questions)
    return pool


def save_question_pool(remaining: list[dict], questions: list[dict]) -> None:
    try:
        progress_path().write_text(
            json.dumps(
                {
                    "bank_sig": bank_signature(questions),
                    "remaining": [question_key(q) for q in remaining],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def load_config() -> tuple[int, list[dict]]:
    data = json.loads(resolve_questions_path().read_text(encoding="utf-8"))
    minutes = float(data.get("interval_minutes", 3))
    interval_ms = max(10, int(minutes * 60 * 1000))
    questions = dedupe_questions(data.get("questions") or [])
    if not questions:
        raise ValueError("questions.json 에 문제가 없습니다.")
    return interval_ms, questions


class QuizAlertApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.interval_ms, self.questions = load_config()
        self.interval_label = self._format_interval()
        self.remaining: list[dict] = load_question_pool(self.questions)
        self.quiz_open = False
        self.viewed_count = 0
        self.next_at = 0.0
        self.keep_job: str | None = None
        self.tick_job: str | None = None
        self.tip_job: str | None = None
        self.show_job: str | None = None
        self.tip_pool: list[str] = []
        self.tip_index = 0

        self.overlay: tk.Toplevel | None = None
        self.source_label: tk.Label | None = None
        self.pixel_surf: PixelSurf | None = None
        self.art_wrap: tk.Frame | None = None
        self.caption_label: tk.Label | None = None
        self.body_row: tk.Frame | None = None
        self.left_pane: tk.Frame | None = None
        self.right_pane: tk.Frame | None = None
        self.question_label: tk.Label | None = None
        self.question_image_label: tk.Label | None = None
        self.explain_image_label: tk.Label | None = None
        self.feedback: tk.Label | None = None
        self.reveal_btn: tk.Button | None = None
        self.explain_frame: tk.Frame | None = None
        self.explain_text: tk.Text | None = None
        self.notes_frame: tk.Frame | None = None
        self.notes_text: tk.Text | None = None
        self.close_btn: tk.Button | None = None
        self.current_item: dict | None = None
        self.locked = False  # 풀이 확인 후 True → 닫기 가능
        self._photo_q: object | None = None
        self._photo_a: object | None = None
        self._split_layout = False
        self._card_wraplength = 720

        self._setup_root()
        self._setup_wait_bar()
        # 시작 직후 대기 없이 바로 1문제 표시
        self.root.after_idle(self.show_quiz)

    def _format_interval(self) -> str:
        seconds = self.interval_ms / 1000
        if seconds >= 60 and abs(seconds / 60 - round(seconds / 60)) < 0.01:
            n = int(round(seconds / 60))
            return f"{n}분"
        return f"{int(seconds)}초"

    def _setup_root(self) -> None:
        self.root.title("9급 전기직 기출 알림")
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

    def _setup_wait_bar(self) -> None:
        self.wait = tk.Toplevel(self.root)
        self.wait.overrideredirect(True)
        self.wait.attributes("-topmost", True)
        self.wait.configure(bg=CARD)
        self.wait.withdraw()

        wrap = tk.Frame(
            self.wait,
            bg=CARD,
            padx=16,
            pady=12,
            highlightthickness=1,
            highlightbackground=CARD_LINE,
        )
        wrap.pack()

        tk.Label(
            wrap,
            text="다음 기출",
            fg=MUTED,
            bg=CARD,
            font=("Malgun Gothic", 9),
        ).pack(anchor="center")

        self.wait_time_label = tk.Label(
            wrap,
            text="00:00",
            fg=TEXT,
            bg=CARD,
            font=("Consolas", 22, "bold"),
        )
        self.wait_time_label.pack(anchor="center", pady=(2, 6))

        tip_box = tk.Frame(
            wrap,
            bg="#121826",
            highlightthickness=1,
            highlightbackground="#2f3b55",
            padx=10,
            pady=8,
        )
        tip_box.pack(fill="x", pady=(0, 8))

        tk.Label(
            tip_box,
            text="깨알 공식",
            fg=TIP_ACCENT,
            bg="#121826",
            font=("Malgun Gothic", 8, "bold"),
        ).pack(anchor="w")

        self.tip_label = tk.Label(
            tip_box,
            text="V = IR  ·  옴의 법칙",
            fg=TIP_ACCENT,
            bg="#121826",
            wraplength=200,
            justify="center",
            font=("Consolas", 10),
        )
        self.tip_label.pack(anchor="center", pady=(4, 0))

        self.wait_label = tk.Label(
            wrap,
            text="확인 0",
            fg=MUTED,
            bg=CARD,
            font=("Malgun Gothic", 9),
        )
        self.wait_label.pack(anchor="center", pady=(0, 8))

        btn_row = tk.Frame(wrap, bg=CARD)
        btn_row.pack(anchor="center")

        now_btn = tk.Button(
            btn_row,
            text="바로 풀기",
            command=self.start_quiz_now,
            bg="#24304a",
            fg=TEXT,
            activebackground=ACCENT,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            font=("Malgun Gothic", 9, "bold"),
        )
        now_btn.pack(side="left", padx=(0, 6))

        random_btn = tk.Button(
            btn_row,
            text="Random",
            command=self.shuffle_questions,
            bg="#2a2448",
            fg=TEXT,
            activebackground="#6c5ce7",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            font=("Malgun Gothic", 9, "bold"),
        )
        random_btn.pack(side="left", padx=(0, 6))

        quit_btn = tk.Button(
            btn_row,
            text="종료",
            command=self.quit_app,
            bg="#3a2430",
            fg=TEXT,
            activebackground=WRONG,
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            font=("Malgun Gothic", 9, "bold"),
        )
        quit_btn.pack(side="left")

        def _ignore_wait_click(_event: tk.Event) -> str:
            return "break"

        for widget in (
            self.wait,
            wrap,
            tip_box,
            self.wait_time_label,
            self.tip_label,
            self.wait_label,
        ):
            widget.bind("<Button-1>", _ignore_wait_click)
            widget.bind("<ButtonPress-1>", _ignore_wait_click)
            widget.bind("<ButtonRelease-1>", _ignore_wait_click)

    def _apply_wait_bar_style(self) -> None:
        self.wait.update_idletasks()
        set_window_no_activate(self.wait.winfo_id())

    def _place_wait_bar(self) -> None:
        self.wait.update_idletasks()
        w = self.wait.winfo_reqwidth()
        h = self.wait.winfo_reqheight()
        sw = self.wait.winfo_screenwidth()
        x = sw - w - 24
        y = 24
        self.wait.geometry(f"{w}x{h}+{x}+{y}")
        self._apply_wait_bar_style()

    def next_question(self) -> dict:
        if not self.remaining:
            self.remaining = list(self.questions)
            random.shuffle(self.remaining)
        item = self.remaining.pop(random.randrange(len(self.remaining)))
        save_question_pool(self.remaining, self.questions)
        return item

    def shuffle_questions(self) -> None:
        """남은 문제 순서를 다시 섞는다. 대기 막대의 Random 버튼에서 호출한다."""
        if self.quiz_open:
            return
        if not self.remaining:
            self.remaining = list(self.questions)
        random.shuffle(self.remaining)
        save_question_pool(self.remaining, self.questions)
        left = len(self.remaining)
        self.wait_label.configure(text=f"섞음 · 남은 {left}")

    def _is_image_item(self, item: dict | None = None) -> bool:
        item = item or self.current_item
        if not item:
            return False
        return bool(item.get("image_mode") or item.get("q_image"))

    def _image_max_size(self, *, pane: str = "single") -> tuple[int, int]:
        """화면 기준으로 잘리지 않게 맞출 최대 가로·세로. pane=left/right 는 좌우 분할용."""
        sw = max(640, self.root.winfo_screenwidth())
        sh = max(480, self.root.winfo_screenheight())
        if pane in ("left", "right", "split"):
            # 좌·우 각각 ~44% 폭, 세로 ~62% — 문제/해설을 크게 나란히 표시
            return max(420, int(sw * 0.44)), max(360, int(sh * 0.62))
        return max(640, int(sw * 0.78)), max(280, int(sh * 0.42))

    def _load_photo(self, relative: str | None, max_w: int, max_h: int):
        """이미지를 비율 유지로 max 박스 안에 맞춘다 (자르지 않음). Pillow 우선."""
        if not relative:
            return None
        path = resolve_media_path(relative)
        if path is None:
            return None
        if Image is not None and ImageTk is not None:
            try:
                with Image.open(path) as src:
                    im = src.convert("RGBA") if src.mode in ("P", "LA", "RGBA") else src.convert("RGB")
                    w, h = im.size
                    if w <= 0 or h <= 0:
                        return None
                    scale = min(max_w / w, max_h / h, 1.0)
                    if scale < 1.0:
                        im = im.resize(
                            (max(1, int(w * scale)), max(1, int(h * scale))),
                            Image.Resampling.LANCZOS,
                        )
                    return ImageTk.PhotoImage(im)
            except Exception:
                pass
        try:
            img = tk.PhotoImage(file=str(path))
            w, h = img.width(), img.height()
            if w <= 0 or h <= 0:
                return None
            if w > max_w or h > max_h:
                factor = max(1, math.ceil(max(w / max_w, h / max_h)))
                img = img.subsample(factor, factor)
            return img
        except tk.TclError:
            return None
        except Exception:
            return None

    def _apply_wraplengths(self, wrap: int) -> None:
        self._card_wraplength = wrap
        if self.caption_label is not None:
            self.caption_label.configure(wraplength=wrap)
        if self.question_label is not None:
            self.question_label.configure(wraplength=wrap)
        if self.feedback is not None:
            self.feedback.configure(wraplength=wrap)

    def _set_split_layout(self, split: bool) -> None:
        """문제(왼쪽) / 풀이(오른쪽) 분할. 풀이 전에는 단일 열."""
        if self.body_row is None or self.left_pane is None or self.right_pane is None:
            return
        self._split_layout = split
        self.left_pane.pack_forget()
        self.right_pane.pack_forget()
        if split:
            self._apply_wraplengths(max(360, int(self.root.winfo_screenwidth() * 0.40)))
            self.left_pane.pack(side="left", fill="both", expand=True, padx=(0, 10))
            self.right_pane.pack(side="left", fill="both", expand=True, padx=(10, 0))
        else:
            self._apply_wraplengths(720)
            self.left_pane.pack(side="left", fill="both", expand=True)
            self.right_pane.pack_forget()

    def show_quiz(self) -> None:
        if self.quiz_open:
            return
        self.quiz_open = True
        self.locked = False
        self._photo_q = None
        self._photo_a = None
        self._cancel_show_job()
        if self.tick_job:
            self.root.after_cancel(self.tick_job)
            self.tick_job = None
        self._stop_tip_rotation()
        self.wait.withdraw()

        item = self.next_question()
        self.current_item = item

        if self.overlay is None:
            self._build_overlay()
        assert self.overlay is not None
        assert self.source_label is not None
        assert self.question_label is not None
        assert self.feedback is not None
        assert self.reveal_btn is not None
        assert self.explain_frame is not None
        assert self.explain_text is not None
        assert self.notes_frame is not None
        assert self.notes_text is not None
        assert self.close_btn is not None

        self.source_label.configure(text=item.get("source", "9급 전기직 기출"))
        image_mode = self._is_image_item(item)

        if self.art_wrap is not None:
            if image_mode:
                self.art_wrap.pack_forget()
            else:
                self.art_wrap.pack(fill="x", pady=(10, 6))
        if self.caption_label is not None:
            if image_mode:
                self.caption_label.pack_forget()
            else:
                self.caption_label.pack(anchor="w", pady=(2, 8))
                if self.pixel_surf is not None:
                    render_visual(self.pixel_surf, item.get("visual"), item)
                self.caption_label.configure(
                    text=item.get("caption") or "8비트 그림: 이 문제가 말하는 상황"
                )

        # 문제(왼) / 필기·풀이(오른) — 처음부터 분할해 필기 공간을 확보
        self._set_split_layout(True)

        if self.question_image_label is not None:
            if image_mode:
                max_w, max_h = self._image_max_size(pane="left")
                self._photo_q = self._load_photo(item.get("q_image"), max_w=max_w, max_h=max_h)
                if self._photo_q is not None:
                    self.question_image_label.configure(image=self._photo_q, text="")
                    self.question_image_label.pack(anchor="nw", pady=(10, 8))
                    self.question_label.configure(text="문제를 풀고, 준비가 되면 풀이 보기를 누르세요.")
                else:
                    self.question_image_label.pack_forget()
                    self.question_label.configure(
                        text="문제 이미지를 불러오지 못했습니다. exam_images 폴더를 확인하세요."
                    )
            else:
                self.question_image_label.pack_forget()
                self.question_label.configure(text=item["q"])
        else:
            self.question_label.configure(text=item.get("q", ""))

        self.feedback.configure(
            text="필기란에 자유롭게 타이핑하세요. 풀이를 확인해야 창을 닫을 수 있습니다.",
            fg=MUTED,
        )
        self.reveal_btn.configure(state="normal")
        self.reveal_btn.pack(fill="x", pady=(12, 0))

        self.explain_text.configure(state="normal")
        self.explain_text.delete("1.0", "end")
        self.explain_text.insert("1.0", "『풀이 보기』를 누르면 해설이 여기에 표시됩니다.")
        self.explain_text.configure(state="disabled")
        if self.explain_image_label is not None:
            self.explain_image_label.pack_forget()
            self.explain_image_label.configure(image="", text="")
        self.notes_text.delete("1.0", "end")
        self.explain_frame.pack(fill="both", expand=True, pady=(0, 0))
        self.notes_frame.pack(fill="x", pady=(10, 0))
        self.close_btn.place_forget()

        self._cover_all_screens()
        self.overlay.deiconify()
        self.overlay.lift()
        self.overlay.attributes("-topmost", True)
        self.root.update_idletasks()
        force_foreground(self.overlay.winfo_id())
        self.notes_text.focus_set()
        beep_alert()
        self._keep_on_top()

    def _build_overlay(self) -> None:
        win = tk.Toplevel(self.root)
        self.overlay = win
        win.withdraw()
        win.overrideredirect(True)
        win.configure(bg=BG)
        win.attributes("-topmost", True)
        win.protocol("WM_DELETE_WINDOW", lambda: None)
        for seq in ("<Alt-F4>", "<Escape>", "<Control-w>", "<Control-F4>"):
            win.bind(seq, lambda e: "break")
        win.bind("<Key>", self._on_key)

        outer = tk.Frame(win, bg=BG)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = tk.Frame(
            outer,
            bg=CARD,
            padx=28,
            pady=22,
            highlightthickness=1,
            highlightbackground=CARD_LINE,
        )
        card.pack()

        tk.Label(
            card,
            text="9급 전기직 기출  ·  알림 퀴즈",
            fg=ACCENT,
            bg=CARD,
            font=("Malgun Gothic", 11, "bold"),
        ).pack(anchor="w")

        self.source_label = tk.Label(
            card,
            text="",
            fg=MUTED,
            bg=CARD,
            font=("Malgun Gothic", 10),
        )
        self.source_label.pack(anchor="w", pady=(6, 0))

        self.body_row = tk.Frame(card, bg=CARD)
        self.body_row.pack(fill="both", expand=True, pady=(8, 0))

        self.left_pane = tk.Frame(self.body_row, bg=CARD)
        self.right_pane = tk.Frame(self.body_row, bg=CARD)
        self.left_pane.pack(side="left", fill="both", expand=True)

        self.art_wrap = tk.Frame(
            self.left_pane, bg="#0a0618", highlightthickness=2, highlightbackground="#f8d030"
        )
        self.art_wrap.pack(fill="x", pady=(10, 6))
        art_canvas = tk.Canvas(self.art_wrap, highlightthickness=0, bd=0)
        art_canvas.pack()
        self.pixel_surf = PixelSurf(art_canvas, scale=4, w=160, h=58)
        self.caption_label = tk.Label(
            self.left_pane,
            text="",
            fg="#f8d030",
            bg=CARD,
            wraplength=self._card_wraplength,
            justify="left",
            font=("Malgun Gothic", 10),
        )
        self.caption_label.pack(anchor="w", pady=(2, 8))

        self.question_image_label = tk.Label(self.left_pane, bg=CARD, bd=0)
        self.question_label = tk.Label(
            self.left_pane,
            text="",
            fg=TEXT,
            bg=CARD,
            wraplength=self._card_wraplength,
            justify="left",
            font=("Malgun Gothic", 15, "bold"),
        )
        self.question_label.pack(anchor="w", pady=(8, 12))

        self.reveal_btn = tk.Button(
            self.left_pane,
            text="풀이 보기",
            command=self.reveal_solution,
            bg=ACCENT,
            fg="white",
            activebackground="#8aa4ff",
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=14,
            pady=12,
            cursor="hand2",
            font=("Malgun Gothic", 13, "bold"),
        )
        self.reveal_btn.pack(fill="x", pady=(12, 0))

        self.feedback = tk.Label(
            self.left_pane,
            text="",
            fg=MUTED,
            bg=CARD,
            wraplength=self._card_wraplength,
            justify="left",
            font=("Malgun Gothic", 11),
        )
        self.feedback.pack(anchor="w", pady=(14, 0))

        self.explain_frame = tk.Frame(
            self.right_pane, bg="#121826", highlightthickness=1, highlightbackground="#2f3b55"
        )
        head = tk.Label(
            self.explain_frame,
            text="해설 · 풀이",
            fg=OK,
            bg="#121826",
            font=("Malgun Gothic", 10, "bold"),
        )
        head.pack(anchor="w", padx=12, pady=(10, 0))
        self.explain_image_label = tk.Label(self.explain_frame, bg="#121826", bd=0)
        self.explain_text = tk.Text(
            self.explain_frame,
            height=8,
            width=48,
            wrap="word",
            bg="#121826",
            fg=TEXT,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            font=("Malgun Gothic", 11),
        )
        self.explain_text.pack(fill="both", expand=True)
        self.explain_text.configure(state="disabled")

        self.notes_frame = tk.Frame(
            self.right_pane, bg="#10161f", highlightthickness=1, highlightbackground="#3a465e"
        )
        notes_head = tk.Label(
            self.notes_frame,
            text="직접 타이핑 · 필기",
            fg=ACCENT,
            bg="#10161f",
            font=("Malgun Gothic", 10, "bold"),
        )
        notes_head.pack(anchor="w", padx=12, pady=(10, 0))
        self.notes_text = tk.Text(
            self.notes_frame,
            height=6,
            width=48,
            wrap="word",
            bg="#10161f",
            fg=TEXT,
            insertbackground=ACCENT,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            font=("Malgun Gothic", 11),
            undo=True,
        )
        self.notes_text.pack(fill="both", expand=True, pady=(0, 4))
        self.notes_text.bind("<KeyPress>", self._on_notes_key)

        self.action_slot = tk.Frame(card, bg=CARD)
        self.action_slot.pack(fill="x")

        self.close_btn = tk.Button(
            win,
            text=f"확인 후 닫기\n{self.interval_label} 뒤에 다시 출제",
            command=self.close_quiz,
            bg=OK,
            fg="#0b0d12",
            activebackground="#63e6a4",
            activeforeground="#0b0d12",
            relief="flat",
            bd=0,
            padx=18,
            pady=14,
            cursor="hand2",
            justify="center",
            font=("Malgun Gothic", 12, "bold"),
        )

        tk.Label(
            card,
            text="필기는 언제든 가능합니다.  풀이 보기 후 Enter/Space 로 닫을 수 있습니다.",
            fg="#667085",
            bg=CARD,
            font=("Malgun Gothic", 9),
        ).pack(anchor="w", pady=(10, 0))

    def _cover_all_screens(self) -> None:
        assert self.overlay is not None
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.overlay.geometry(f"{sw}x{sh}+0+0")

    def _keep_on_top(self) -> None:
        if not self.quiz_open or self.overlay is None:
            return
        try:
            self.overlay.lift()
            self.overlay.attributes("-topmost", True)
            # 필기 중에는 포커스를 빼앗지 않는다
            if not self._notes_has_focus():
                force_foreground(self.overlay.winfo_id())
        except tk.TclError:
            return
        self.keep_job = self.root.after(500, self._keep_on_top)

    def _notes_has_focus(self) -> bool:
        if self.notes_text is None:
            return False
        try:
            return self.root.focus_get() is self.notes_text
        except tk.TclError:
            return False

    def _on_notes_key(self, event: tk.Event) -> None:
        skip = {
            "Shift_L",
            "Shift_R",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
            "Caps_Lock",
            "Hangul",
            "Hanja",
            "Win_L",
            "Win_R",
            "Escape",
        }
        if event.keysym in skip:
            return
        if event.char or event.keysym in ("BackSpace", "Delete", "Return", "Tab", "space", "Left", "Right", "Up", "Down"):
            if event.keysym in ("Left", "Right", "Up", "Down"):
                return
            beep_type()

    def _on_key(self, event: tk.Event) -> str | None:
        if self._notes_has_focus():
            return None
        if event.keysym in ("Return", "space"):
            if self.locked:
                self.close_quiz()
            else:
                self.reveal_solution()
            return "break"
        return "break"

    def reveal_solution(self) -> None:
        if not self.quiz_open or self.locked or self.current_item is None:
            return
        self.locked = True
        self.viewed_count += 1
        if self.reveal_btn is not None:
            self.reveal_btn.configure(state="disabled")
        if self.feedback is not None:
            self.feedback.configure(
                text=f"풀이를 확인했습니다. 닫으면 {self.interval_label} 뒤에 다시 나옵니다.",
                fg=OK,
            )
        self._show_explain()
        if winsound:
            try:
                winsound.MessageBeep(winsound.MB_OK)
            except Exception:
                pass

    def _show_explain(self) -> None:
        assert self.explain_frame is not None
        assert self.explain_text is not None
        assert self.notes_frame is not None
        assert self.notes_text is not None
        assert self.close_btn is not None
        item = self.current_item or {}
        text = item.get("explain") or ""
        image_mode = self._is_image_item(item)

        self._set_split_layout(True)

        if self.explain_image_label is not None:
            self.explain_image_label.pack_forget()
            self._photo_a = None
            if image_mode:
                max_w, max_h = self._image_max_size(pane="right")
                self._photo_a = self._load_photo(
                    item.get("a_image"),
                    max_w=max_w,
                    max_h=max_h,
                )
                if self._photo_a is not None:
                    self.explain_image_label.configure(image=self._photo_a, text="")
                    self.explain_image_label.pack(
                        anchor="nw",
                        fill="x",
                        padx=8,
                        pady=(6, 4),
                        before=self.explain_text,
                    )
                    if not text:
                        text = "위 해설 이미지를 확인하세요."

        if not text:
            text = "해설이 없습니다."
        self.explain_text.configure(state="normal")
        self.explain_text.delete("1.0", "end")
        self.explain_text.insert("1.0", text)
        self.explain_text.configure(state="disabled")
        # 필기 내용은 지우지 않는다 — 처음부터 타이핑 가능
        self.explain_frame.pack(fill="both", expand=True, pady=(0, 0))
        self.notes_frame.pack(fill="x", pady=(10, 0))
        self._place_close_btn()
        self.notes_text.focus_set()

    def _place_close_btn(self) -> None:
        """카드 높이와 상관없이 화면 오른쪽에 닫기 버튼을 고정한다."""
        assert self.overlay is not None
        assert self.close_btn is not None
        self.overlay.update_idletasks()
        self.close_btn.place(relx=1.0, rely=0.5, anchor="e", x=-28)

    def close_quiz(self) -> None:
        if not self.locked:
            return
        if self.keep_job:
            self.root.after_cancel(self.keep_job)
            self.keep_job = None
        self.quiz_open = False
        self._photo_q = None
        self._photo_a = None
        if self.overlay is not None:
            self.overlay.withdraw()
        self.next_at = time.monotonic() + (self.interval_ms / 1000)
        self._place_wait_bar()
        self.wait.deiconify()
        self._apply_wait_bar_style()
        self._start_tip_rotation()
        self._tick_wait()
        self.show_job = self.root.after(self.interval_ms, self.show_quiz)

    def start_quiz_now(self) -> None:
        if self.quiz_open:
            return
        self._cancel_show_job()
        self.show_quiz()

    def _cancel_show_job(self) -> None:
        if self.show_job:
            self.root.after_cancel(self.show_job)
            self.show_job = None

    def _next_tip(self) -> str:
        if not self.tip_pool or self.tip_index >= len(self.tip_pool):
            self.tip_pool = list(MINI_TIPS)
            random.shuffle(self.tip_pool)
            self.tip_index = 0
        tip = self.tip_pool[self.tip_index]
        self.tip_index += 1
        return tip

    def _show_tip(self) -> None:
        if self.quiz_open or not hasattr(self, "tip_label"):
            return
        self.tip_label.configure(text=self._next_tip())

    def _start_tip_rotation(self) -> None:
        self._stop_tip_rotation()
        self.tip_pool = list(MINI_TIPS)
        random.shuffle(self.tip_pool)
        self.tip_index = 0
        self._show_tip()
        self.tip_job = self.root.after(TIP_ROTATE_MS, self._rotate_tip)

    def _rotate_tip(self) -> None:
        if self.quiz_open:
            return
        self._show_tip()
        self.tip_job = self.root.after(TIP_ROTATE_MS, self._rotate_tip)

    def _stop_tip_rotation(self) -> None:
        if self.tip_job:
            self.root.after_cancel(self.tip_job)
            self.tip_job = None

    def _tick_wait(self) -> None:
        if self.quiz_open:
            return
        left = max(0, int(self.next_at - time.monotonic()))
        m, s = divmod(left, 60)
        self.wait_time_label.configure(text=f"{m:02d}:{s:02d}")
        self.wait_label.configure(text=f"확인 {self.viewed_count}")
        self.tick_job = self.root.after(250, self._tick_wait)

    def quit_app(self) -> None:
        if self.quiz_open:
            return
        self._stop_tip_rotation()
        self._cancel_show_job()
        if self.tick_job:
            self.root.after_cancel(self.tick_job)
            self.tick_job = None
        self.root.destroy()


def show_error(message: str) -> None:
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.MessageBoxW(None, message, "9급 전기직 기출 알림", 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def main() -> None:
    enable_dpi_awareness()
    if not ensure_single_instance():
        ctypes.windll.user32.MessageBoxW(
            None,
            "퀴즈 알림이 이미 실행 중입니다.\n오른쪽 위 작은 막대에서 종료한 뒤 다시 실행하세요.",
            "9급 전기직 기출 알림",
            0x40,
        )
        return
    questions = resolve_questions_path()
    if not questions.is_file():
        show_error(f"문제 파일이 없습니다.\n{questions}")
        raise SystemExit(f"문제 파일이 없습니다: {questions}")

    try:
        root = tk.Tk()
        default = tkfont.nametofont("TkDefaultFont")
        default.configure(family="Malgun Gothic", size=10)
        QuizAlertApp(root)
        root.mainloop()
    except Exception as exc:
        show_error(f"실행 중 오류가 났습니다.\n{exc}")
        raise


if __name__ == "__main__":
    main()
