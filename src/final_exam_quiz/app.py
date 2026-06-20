from __future__ import annotations

import json
import random
import sys
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import font as tkfont
from typing import Iterable

from . import __version__


APP_TITLE = "形势与政策 I 选择题练习"
DATA_FILE = "questions.json"
MISTAKES_FILE = "mistakes.json"


@dataclass(frozen=True)
class Question:
    id: str
    topic: str
    kind: str
    question: str
    options: list[str]
    answers: set[int]
    explanation: str

    @property
    def is_multiple(self) -> bool:
        return self.kind == "multiple"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", app_root()))
    candidate = base.joinpath(*parts)
    if candidate.exists():
        return candidate
    return app_root().joinpath(*parts)


def user_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "user_data"
    return app_root() / "user_data"


def load_questions() -> list[Question]:
    data_path = resource_path("data", DATA_FILE)
    raw = json.loads(data_path.read_text(encoding="utf-8"))
    questions = [
        Question(
            id=item["id"],
            topic=item["topic"],
            kind=item["kind"],
            question=item["question"],
            options=item["options"],
            answers=set(item["answers"]),
            explanation=item["explanation"],
        )
        for item in raw
    ]
    return questions


def load_mistake_ids() -> set[str]:
    path = user_data_dir() / MISTAKES_FILE
    if not path.exists():
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    return set(payload.get("mistakes", []))


def save_mistake_ids(ids: Iterable[str]) -> None:
    directory = user_data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / MISTAKES_FILE
    payload = {"version": __version__, "mistakes": sorted(set(ids))}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class ScrollFrame(tk.Frame):
    def __init__(self, master: tk.Widget, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#f6f7fb")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg="#f6f7fb")
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", self._sync_scrollregion)
        self.canvas.bind("<Configure>", self._sync_width)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _sync_scrollregion(self, _event: tk.Event) -> None:
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _sync_width(self, event: tk.Event) -> None:
        self.canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.winfo_viewable():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def top(self) -> None:
        self.canvas.yview_moveto(0)


class QuizApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} v{__version__}")
        self.root.geometry("1060x720")
        self.root.minsize(900, 620)
        self.root.configure(bg="#f6f7fb")

        self.questions = load_questions()
        self.question_map = {q.id: q for q in self.questions}
        self.session: list[Question] = []
        self.index = 0
        self.current_selection: set[int] = set()
        self.session_wrong_ids: set[str] = set()
        self.session_answered = 0
        self.session_correct = 0
        self.mode = "all"
        self.answered_current = False

        self._setup_fonts()
        self._build_layout()
        self.show_home()

    def _setup_fonts(self) -> None:
        font_path = resource_path("assets", "NotoSansSC-VF.ttf")
        if sys.platform == "win32" and font_path.exists():
            try:
                import ctypes

                ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
            except Exception:
                pass
        family = "Noto Sans SC"
        available = set(tkfont.families(self.root))
        if family not in available:
            family = "Microsoft YaHei" if "Microsoft YaHei" in available else "SimHei"
        self.fonts = {
            "title": (family, 24, "bold"),
            "subtitle": (family, 12),
            "body": (family, 13),
            "body_bold": (family, 13, "bold"),
            "small": (family, 10),
            "button": (family, 12, "bold"),
            "option": (family, 12),
        }

    def _build_layout(self) -> None:
        self.header = tk.Frame(self.root, bg="#12263a", height=70)
        self.header.pack(fill="x")
        self.title_label = tk.Label(
            self.header,
            text=APP_TITLE,
            bg="#12263a",
            fg="white",
            font=self.fonts["title"],
            padx=24,
        )
        self.title_label.pack(side="left", fill="y")
        self.status_label = tk.Label(
            self.header,
            text=f"v{__version__}",
            bg="#12263a",
            fg="#d6e4f0",
            font=self.fonts["subtitle"],
            padx=24,
        )
        self.status_label.pack(side="right", fill="y")

        self.content = ScrollFrame(self.root)
        self.content.pack(fill="both", expand=True)

        self.footer = tk.Frame(self.root, bg="white", height=78, padx=20, pady=14)
        self.footer.pack(fill="x")

    def clear(self) -> None:
        for child in self.content.inner.winfo_children():
            child.destroy()
        for child in self.footer.winfo_children():
            child.destroy()
        self.content.top()

    def button(self, master: tk.Widget, text: str, command, primary: bool = False, disabled: bool = False) -> tk.Button:
        bg = "#1d6fd8" if primary else "#e8edf4"
        fg = "white" if primary else "#19324a"
        active = "#1558ad" if primary else "#d9e2ef"
        return tk.Button(
            master,
            text=text,
            command=command,
            font=self.fonts["button"],
            bg=bg,
            fg=fg,
            activebackground=active,
            activeforeground=fg,
            disabledforeground="#94a3b8",
            relief="flat",
            padx=18,
            pady=10,
            cursor="hand2",
            state="disabled" if disabled else "normal",
        )

    def card(self, master: tk.Widget, padx: int = 22, pady: int = 18) -> tk.Frame:
        frame = tk.Frame(master, bg="white", padx=padx, pady=pady, highlightthickness=1, highlightbackground="#d9e2ec")
        frame.pack(fill="x", padx=24, pady=12)
        return frame

    def show_home(self) -> None:
        self.clear()
        wrong_count = len(load_mistake_ids())
        card = self.card(self.content.inner, padx=28, pady=24)
        tk.Label(
            card,
            text="高频专题一、二选择题练习",
            bg="white",
            fg="#102a43",
            font=self.fonts["title"],
            anchor="w",
        ).pack(fill="x")
        intro = (
            "题库来自 PDF 中“浙大校训精神与求是学子的使命”和"
            "“当前国际格局、国家利益与中国特色大国外交”，并参考往年卷固定提法、"
            "辨析题和挖空题的考法整理。"
        )
        tk.Label(
            card,
            text=intro,
            bg="white",
            fg="#486581",
            font=self.fonts["body"],
            anchor="w",
            justify="left",
            wraplength=920,
        ).pack(fill="x", pady=(12, 0))

        stats = self.card(self.content.inner)
        tk.Label(
            stats,
            text=f"当前题库：{len(self.questions)} 题    错题集：{wrong_count} 题",
            bg="white",
            fg="#243b53",
            font=self.fonts["body_bold"],
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            stats,
            text="做完一轮会自动写入错题集。选择“做错题”完成后，会用本轮仍答错的题覆盖原错题集。",
            bg="white",
            fg="#627d98",
            font=self.fonts["body"],
            anchor="w",
            wraplength=920,
            justify="left",
        ).pack(fill="x", pady=(8, 0))

        footer_left = tk.Frame(self.footer, bg="white")
        footer_left.pack(side="left")
        self.button(footer_left, "重新作答所有", lambda: self.start_quiz("all"), primary=True).pack(side="left", padx=(0, 12))
        self.button(footer_left, "只做错题并覆盖", lambda: self.start_quiz("mistakes"), disabled=wrong_count == 0).pack(side="left")
        self.button(self.footer, "退出", self.root.destroy).pack(side="right")

    def start_quiz(self, mode: str) -> None:
        self.mode = mode
        if mode == "mistakes":
            mistake_ids = load_mistake_ids()
            self.session = [self.question_map[qid] for qid in mistake_ids if qid in self.question_map]
        else:
            self.session = list(self.questions)
        random.Random().shuffle(self.session)
        self.index = 0
        self.session_wrong_ids = set()
        self.session_answered = 0
        self.session_correct = 0
        if not self.session:
            self.show_home()
            return
        self.show_question()

    def show_question(self) -> None:
        self.clear()
        self.answered_current = False
        self.current_selection = set()
        q = self.session[self.index]
        self.status_label.configure(
            text=f"{self.index + 1}/{len(self.session)}    正确 {self.session_correct} / 已答 {self.session_answered}"
        )

        topic = self.card(self.content.inner, padx=22, pady=14)
        tk.Label(topic, text=q.topic, bg="white", fg="#486581", font=self.fonts["subtitle"], anchor="w").pack(fill="x")

        question_card = self.card(self.content.inner, padx=26, pady=22)
        kind_text = "多选题" if q.is_multiple else "单选题"
        tk.Label(
            question_card,
            text=f"{kind_text}  {self.index + 1}. {q.question}",
            bg="white",
            fg="#102a43",
            font=self.fonts["body_bold"],
            justify="left",
            anchor="w",
            wraplength=920,
        ).pack(fill="x", pady=(0, 14))

        self.option_vars: list[tk.IntVar] = []
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, option in enumerate(q.options):
            var = tk.IntVar(value=0)
            self.option_vars.append(var)
            if q.is_multiple:
                widget = tk.Checkbutton(
                    question_card,
                    text=f"{letters[i]}. {option}",
                    variable=var,
                    command=self._sync_selection,
                    bg="white",
                    fg="#243b53",
                    activebackground="white",
                    font=self.fonts["option"],
                    anchor="w",
                    justify="left",
                    wraplength=860,
                    padx=10,
                    pady=8,
                    selectcolor="#dbeafe",
                )
            else:
                widget = tk.Radiobutton(
                    question_card,
                    text=f"{letters[i]}. {option}",
                    variable=var,
                    value=1,
                    command=lambda idx=i: self._select_single(idx),
                    bg="white",
                    fg="#243b53",
                    activebackground="white",
                    font=self.fonts["option"],
                    anchor="w",
                    justify="left",
                    wraplength=860,
                    padx=10,
                    pady=8,
                    selectcolor="#dbeafe",
                )
            widget.pack(fill="x", pady=2)

        hint = "可选择多个答案" if q.is_multiple else "请选择一个答案"
        tk.Label(question_card, text=hint, bg="white", fg="#829ab1", font=self.fonts["small"], anchor="w").pack(fill="x", pady=(10, 0))

        self.feedback = self.card(self.content.inner, padx=22, pady=14)
        self.feedback.pack_forget()

        self.submit_button = self.button(self.footer, "提交答案", self.submit_answer, primary=True)
        self.submit_button.pack(side="right")
        self.button(self.footer, "返回首页", self.show_home).pack(side="left")

    def _select_single(self, index: int) -> None:
        for i, var in enumerate(self.option_vars):
            var.set(1 if i == index else 0)
        self.current_selection = {index}

    def _sync_selection(self) -> None:
        self.current_selection = {i for i, var in enumerate(self.option_vars) if var.get()}

    def submit_answer(self) -> None:
        if self.answered_current:
            return
        self._sync_selection()
        if not self.current_selection:
            self.show_message("请先选择答案。", ok=False)
            return

        q = self.session[self.index]
        correct = self.current_selection == q.answers
        self.session_answered += 1
        if correct:
            self.session_correct += 1
        else:
            self.session_wrong_ids.add(q.id)
        self.answered_current = True
        self.show_message(self.feedback_text(q, correct), ok=correct)
        self.submit_button.configure(state="disabled")
        self.button(self.footer, "下一题" if self.index + 1 < len(self.session) else "查看结果", self.next_question, primary=True).pack(side="right", padx=(0, 12))

    def feedback_text(self, q: Question, correct: bool) -> str:
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        answer = "、".join(f"{letters[i]}. {q.options[i]}" for i in sorted(q.answers))
        selected = "、".join(f"{letters[i]}. {q.options[i]}" for i in sorted(self.current_selection))
        status = "回答正确" if correct else "回答错误"
        return f"{status}\n你的答案：{selected}\n正确答案：{answer}\n解析：{q.explanation}"

    def show_message(self, text: str, ok: bool) -> None:
        for child in self.feedback.winfo_children():
            child.destroy()
        self.feedback.pack(fill="x", padx=24, pady=12)
        color = "#0f766e" if ok else "#b42318"
        bg = "#ecfdf5" if ok else "#fff1f2"
        self.feedback.configure(bg=bg, highlightbackground="#b7e4d8" if ok else "#fecdd3")
        tk.Label(
            self.feedback,
            text=text,
            bg=bg,
            fg=color,
            font=self.fonts["body"],
            justify="left",
            anchor="w",
            wraplength=920,
        ).pack(fill="x")

    def next_question(self) -> None:
        if self.index + 1 < len(self.session):
            self.index += 1
            self.show_question()
        else:
            self.finish_session()

    def finish_session(self) -> None:
        if self.mode == "mistakes":
            save_mistake_ids(self.session_wrong_ids)
        else:
            save_mistake_ids(self.session_wrong_ids)
        self.show_result()

    def show_result(self) -> None:
        self.clear()
        self.status_label.configure(text=f"v{__version__}")
        total = len(self.session)
        wrong = len(self.session_wrong_ids)
        score = 0 if total == 0 else round((total - wrong) / total * 100)
        card = self.card(self.content.inner, padx=28, pady=24)
        tk.Label(card, text="本轮完成", bg="white", fg="#102a43", font=self.fonts["title"], anchor="w").pack(fill="x")
        tk.Label(
            card,
            text=f"得分：{score}    正确：{total - wrong}    错题：{wrong}    总题数：{total}",
            bg="white",
            fg="#243b53",
            font=self.fonts["body_bold"],
            anchor="w",
        ).pack(fill="x", pady=(14, 8))
        saved_note = "错题集已覆盖为本轮仍答错的题。" if self.mode == "mistakes" else "错题集已更新为本轮答错的题。"
        tk.Label(card, text=saved_note, bg="white", fg="#627d98", font=self.fonts["body"], anchor="w").pack(fill="x")

        if wrong:
            wrong_card = self.card(self.content.inner, padx=22, pady=18)
            tk.Label(wrong_card, text="错题列表", bg="white", fg="#102a43", font=self.fonts["body_bold"], anchor="w").pack(fill="x")
            for qid in sorted(self.session_wrong_ids):
                q = self.question_map[qid]
                tk.Label(
                    wrong_card,
                    text=f"- {q.question}",
                    bg="white",
                    fg="#486581",
                    font=self.fonts["body"],
                    anchor="w",
                    justify="left",
                    wraplength=920,
                ).pack(fill="x", pady=(8, 0))

        self.button(self.footer, "重新作答所有", lambda: self.start_quiz("all"), primary=True).pack(side="left", padx=(0, 12))
        self.button(self.footer, "做错题并覆盖", lambda: self.start_quiz("mistakes"), disabled=wrong == 0).pack(side="left")
        self.button(self.footer, "返回首页", self.show_home).pack(side="right")

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    if "--self-test" in sys.argv:
        questions = load_questions()
        assert len(questions) >= 1
        assert resource_path("data", DATA_FILE).exists()
        assert resource_path("assets", "NotoSansSC-VF.ttf").exists()
        print(f"OK: {len(questions)} questions, resources ready")
        return
    QuizApp().run()
