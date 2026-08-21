#!/usr/bin/env python3
"""9급 전기직 기출 알림 퀴즈. 정답을 맞히고 해설을 확인해야 창이 닫힌다."""

from __future__ import annotations

import ctypes
import json
import random
import sys
import time
from pathlib import Path

try:
    import winsound
except ImportError:
    winsound = None

import tkinter as tk
from tkinter import font as tkfont

from pixel_art import PixelSurf, render_visual

APP_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = APP_DIR / "questions.json"
MUTEX_NAME = "Local\\QuizAlertSingleInstance"
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040
ERROR_ALREADY_EXISTS = 183

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


def load_config() -> tuple[int, list[dict]]:
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    minutes = float(data.get("interval_minutes", 3))
    interval_ms = max(10, int(minutes * 60 * 1000))
    questions = data.get("questions") or []
    if not questions:
        raise ValueError("questions.json 에 문제가 없습니다.")
    return interval_ms, questions


class QuizAlertApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.interval_ms, self.questions = load_config()
        self.interval_label = self._format_interval()
        self.remaining: list[dict] = []
        self.quiz_open = False
        self.solved_count = 0
        self.miss_count = 0
        self.next_at = 0.0
        self.keep_job: str | None = None
        self.tick_job: str | None = None

        self.overlay: tk.Toplevel | None = None
        self.source_label: tk.Label | None = None
        self.pixel_surf: PixelSurf | None = None
        self.caption_label: tk.Label | None = None
        self.question_label: tk.Label | None = None
        self.feedback: tk.Label | None = None
        self.choice_buttons: list[tk.Button] = []
        self.explain_frame: tk.Frame | None = None
        self.explain_text: tk.Text | None = None
        self.close_btn: tk.Button | None = None
        self.current_item: dict | None = None
        self.current_answer = 0
        self.locked = False

        self._setup_root()
        self._setup_wait_bar()
        self.root.after(400, self.show_quiz)

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

        wrap = tk.Frame(self.wait, bg=CARD, padx=14, pady=10)
        wrap.pack()

        self.wait_label = tk.Label(
            wrap,
            text="다음 기출 대기 중",
            fg=TEXT,
            bg=CARD,
            font=("Malgun Gothic", 10),
        )
        self.wait_label.pack(side="left", padx=(0, 12))

        quit_btn = tk.Button(
            wrap,
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

        self.wait.bind("<ButtonPress-1>", self._start_move)
        self.wait.bind("<B1-Motion>", self._on_move)
        self.wait_label.bind("<ButtonPress-1>", self._start_move)
        self.wait_label.bind("<B1-Motion>", self._on_move)

    def _place_wait_bar(self) -> None:
        self.wait.update_idletasks()
        w = self.wait.winfo_reqwidth()
        h = self.wait.winfo_reqheight()
        sw = self.wait.winfo_screenwidth()
        x = sw - w - 24
        y = 24
        self.wait.geometry(f"{w}x{h}+{x}+{y}")

    def _start_move(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self.wait.winfo_x()
        self._drag_y = event.y_root - self.wait.winfo_y()

    def _on_move(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.wait.geometry(f"+{x}+{y}")

    def next_question(self) -> dict:
        if not self.remaining:
            self.remaining = list(self.questions)
            random.shuffle(self.remaining)
        return self.remaining.pop()

    def show_quiz(self) -> None:
        if self.quiz_open:
            return
        self.quiz_open = True
        self.locked = False
        if self.tick_job:
            self.root.after_cancel(self.tick_job)
            self.tick_job = None
        self.wait.withdraw()

        item = self.next_question()
        self.current_item = item
        self.current_answer = int(item["answer"])

        if self.overlay is None:
            self._build_overlay()
        assert self.overlay is not None
        assert self.source_label is not None
        assert self.question_label is not None
        assert self.feedback is not None
        assert self.explain_frame is not None
        assert self.explain_text is not None
        assert self.close_btn is not None

        self.source_label.configure(text=item.get("source", "9급 전기직 기출"))
        if self.pixel_surf is not None:
            render_visual(self.pixel_surf, item.get("visual"), item)
        if self.caption_label is not None:
            self.caption_label.configure(
                text=item.get("caption") or "8비트 그림: 이 문제가 말하는 상황"
            )
        self.question_label.configure(text=item["q"])
        self.feedback.configure(text="정답을 고르세요. 맞혀야 창이 닫힙니다.", fg=MUTED)
        choices = item["choices"]
        for i, btn in enumerate(self.choice_buttons):
            if i < len(choices):
                btn.configure(
                    text=f"{i + 1}.  {choices[i]}",
                    state="normal",
                    bg=BTN,
                    fg=TEXT,
                )
                btn.pack(fill="x", pady=5)
            else:
                btn.pack_forget()

        self.explain_text.configure(state="normal")
        self.explain_text.delete("1.0", "end")
        self.explain_text.configure(state="disabled")
        self.explain_frame.pack_forget()
        self.close_btn.pack_forget()

        self._cover_all_screens()
        self.overlay.deiconify()
        self.overlay.lift()
        self.overlay.attributes("-topmost", True)
        self.overlay.focus_force()
        self.root.update_idletasks()
        force_foreground(self.overlay.winfo_id())
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
            padx=40,
            pady=28,
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

        art_wrap = tk.Frame(card, bg="#0a0618", highlightthickness=2, highlightbackground="#f8d030")
        art_wrap.pack(fill="x", pady=(10, 6))
        art_canvas = tk.Canvas(art_wrap, highlightthickness=0, bd=0)
        art_canvas.pack()
        self.pixel_surf = PixelSurf(art_canvas, scale=4, w=160, h=58)
        self.caption_label = tk.Label(
            card,
            text="",
            fg="#f8d030",
            bg=CARD,
            wraplength=720,
            justify="left",
            font=("Malgun Gothic", 10),
        )
        self.caption_label.pack(anchor="w", pady=(2, 8))

        self.question_label = tk.Label(
            card,
            text="",
            fg=TEXT,
            bg=CARD,
            wraplength=720,
            justify="left",
            font=("Malgun Gothic", 16, "bold"),
        )
        self.question_label.pack(anchor="w", pady=(12, 18))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x")
        self.choice_buttons = []
        for i in range(4):
            btn = tk.Button(
                btns,
                text="",
                command=lambda idx=i: self.try_answer(idx),
                bg=BTN,
                fg=TEXT,
                activebackground=BTN_HOVER,
                activeforeground=TEXT,
                relief="flat",
                bd=0,
                padx=14,
                pady=10,
                anchor="w",
                justify="left",
                wraplength=680,
                cursor="hand2",
                font=("Malgun Gothic", 12),
            )
            btn.pack(fill="x", pady=5)
            btn.bind(
                "<Enter>",
                lambda e, b=btn: b.configure(bg=BTN_HOVER) if str(b["state"]) == "normal" else None,
            )
            btn.bind(
                "<Leave>",
                lambda e, b=btn: b.configure(bg=BTN) if str(b["state"]) == "normal" else None,
            )
            self.choice_buttons.append(btn)

        self.feedback = tk.Label(
            card,
            text="",
            fg=MUTED,
            bg=CARD,
            wraplength=720,
            justify="left",
            font=("Malgun Gothic", 11),
        )
        self.feedback.pack(anchor="w", pady=(14, 0))

        self.explain_frame = tk.Frame(card, bg="#121826", highlightthickness=1, highlightbackground="#2f3b55")
        head = tk.Label(
            self.explain_frame,
            text="해설",
            fg=OK,
            bg="#121826",
            font=("Malgun Gothic", 10, "bold"),
        )
        head.pack(anchor="w", padx=12, pady=(10, 0))
        self.explain_text = tk.Text(
            self.explain_frame,
            height=7,
            width=78,
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

        self.action_slot = tk.Frame(card, bg=CARD)
        self.action_slot.pack(fill="x")

        self.close_btn = tk.Button(
            self.action_slot,
            text=f"해설 확인 후 닫기  ·  {self.interval_label} 뒤에 다시 출제",
            command=self.close_quiz,
            bg=OK,
            fg="#0b0d12",
            activebackground="#63e6a4",
            activeforeground="#0b0d12",
            relief="flat",
            bd=0,
            padx=16,
            pady=10,
            cursor="hand2",
            font=("Malgun Gothic", 12, "bold"),
        )

        tk.Label(
            card,
            text="숫자 키 1~4 로도 고를 수 있습니다.  퀴즈 중에는 창을 닫을 수 없습니다.",
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
            force_foreground(self.overlay.winfo_id())
        except tk.TclError:
            return
        self.keep_job = self.root.after(500, self._keep_on_top)

    def _on_key(self, event: tk.Event) -> str | None:
        if self.locked and event.keysym in ("Return", "space"):
            self.close_quiz()
            return "break"
        if event.char in "1234":
            self.try_answer(int(event.char) - 1)
            return "break"
        return "break"

    def try_answer(self, idx: int) -> None:
        if not self.quiz_open or self.locked or self.current_item is None:
            return
        if idx >= len(self.current_item["choices"]):
            return
        if idx == self.current_answer:
            self.locked = True
            self.solved_count += 1
            for i, btn in enumerate(self.choice_buttons):
                if i >= len(self.current_item["choices"]):
                    continue
                btn.configure(state="disabled")
                if i == idx:
                    btn.configure(bg=OK, fg="#0b0d12")
            if self.feedback:
                self.feedback.configure(
                    text=f"정답입니다. 해설을 읽고 닫으면 {self.interval_label} 뒤에 다시 나옵니다.",
                    fg=OK,
                )
            self._show_explain()
            if winsound:
                try:
                    winsound.MessageBeep(winsound.MB_OK)
                except Exception:
                    pass
        else:
            self.miss_count += 1
            btn = self.choice_buttons[idx]
            btn.configure(bg=WRONG)
            if self.feedback:
                self.feedback.configure(text="오답입니다. 다시 골라 주세요.", fg=WRONG)
            if winsound:
                try:
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                except Exception:
                    pass
            self.root.after(280, lambda: btn.configure(bg=BTN) if str(btn["state"]) == "normal" else None)

    def _show_explain(self) -> None:
        assert self.explain_frame is not None
        assert self.explain_text is not None
        assert self.close_btn is not None
        text = (self.current_item or {}).get("explain") or "해설이 없습니다."
        self.explain_text.configure(state="normal")
        self.explain_text.delete("1.0", "end")
        self.explain_text.insert("1.0", text)
        self.explain_text.configure(state="disabled")
        self.explain_frame.pack(fill="x", pady=(12, 0), before=self.action_slot)
        self.close_btn.pack(fill="x", pady=(12, 0))

    def close_quiz(self) -> None:
        if not self.locked:
            return
        if self.keep_job:
            self.root.after_cancel(self.keep_job)
            self.keep_job = None
        self.quiz_open = False
        if self.overlay is not None:
            self.overlay.withdraw()
        self.next_at = time.monotonic() + (self.interval_ms / 1000)
        self._place_wait_bar()
        self.wait.deiconify()
        self._tick_wait()
        self.root.after(self.interval_ms, self.show_quiz)

    def _tick_wait(self) -> None:
        if self.quiz_open:
            return
        left = max(0, int(self.next_at - time.monotonic()))
        m, s = divmod(left, 60)
        self.wait_label.configure(
            text=f"다음 기출 {m:02d}:{s:02d}   ·   정답 {self.solved_count}  오답 {self.miss_count}"
        )
        self.tick_job = self.root.after(250, self._tick_wait)

    def quit_app(self) -> None:
        if self.quiz_open:
            return
        self.root.destroy()


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
    if not QUESTIONS_PATH.exists():
        raise SystemExit(f"문제 파일이 없습니다: {QUESTIONS_PATH}")

    root = tk.Tk()
    default = tkfont.nametofont("TkDefaultFont")
    default.configure(family="Malgun Gothic", size=10)
    QuizAlertApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
