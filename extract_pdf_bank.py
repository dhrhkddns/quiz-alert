# -*- coding: utf-8 -*-
"""Extract every 9급 전기이론/전기기기 question from the Seowongak PDF into the quiz bank."""
from __future__ import annotations

import json
import re
from pathlib import Path

import cv2
import numpy as np

HERE = Path(__file__).resolve().parent
IMG_ROOT = Path(
    r"C:\Users\omyra\Downloads\9급 전기직 전기기기.전기이론"
    r"\images\9급 전기직 전기기기.전기이론"
)
PDF_STEM = "9급 전기직 전기기기.전기이론"
Q_DIR = HERE / "exam_images" / "q"
A_DIR = HERE / "exam_images" / "a"
JSON_PATH = HERE / "questions.json"
REPORT_PATH = HERE / "_extract_report.json"

IRON_OFFSET = 2  # book page 8 -> pdf 10
MACHINE_OFFSET = 306  # book page 2 -> pdf 308
IRON_PDF_END = 305
MACHINE_PDF_END = 512
ANSWER_SCORE_MIN = 0.76


def page_path(n: int) -> Path:
    return IMG_ROOT / f"{PDF_STEM}_{n}.jpg"


def load_gray(n: int):
    p = page_path(n)
    if not p.is_file():
        return None
    return cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_GRAYSCALE)


def load_bgr(n: int):
    p = page_path(n)
    if not p.is_file():
        return None
    return cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)


def imwrite_unicode(path: Path, img) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError(f"encode failed: {path}")
    buf.tofile(str(path))


def make_answer_tmpl():
    g = load_gray(10)
    if g is None:
        raise FileNotFoundError("template page 10 missing")
    return cv2.threshold(g[1088:1114, 78:142], 160, 255, cv2.THRESH_BINARY)[1]


ANSWER_TMPL = None


def find_answer(gray) -> tuple[int, float, int]:
    """Return (y, score, x) of ANSWER word."""
    global ANSWER_TMPL
    if ANSWER_TMPL is None:
        ANSWER_TMPL = make_answer_tmpl()
    _, bw = cv2.threshold(gray, 160, 255, cv2.THRESH_BINARY)
    res = cv2.matchTemplate(bw, ANSWER_TMPL, cv2.TM_CCOEFF_NORMED)
    _, maxv, _, maxl = cv2.minMaxLoc(res)
    return int(maxl[1]), float(maxv), int(maxl[0])


def answer_line_qcount(gray, ay: int, ax: int) -> int:
    """ANSWER 줄의 ①②③④ 개수 = 이 페이지 문항 수."""
    global ANSWER_TMPL
    if ANSWER_TMPL is None:
        ANSWER_TMPL = make_answer_tmpl()
    tw, th = ANSWER_TMPL.shape[1], ANSWER_TMPL.shape[0]
    x0 = ax + tw + 2
    x1 = min(gray.shape[1] - 8, x0 + 560)
    y0 = max(0, ay - 3)
    y1 = min(gray.shape[0], ay + th + 10)
    line = gray[y0:y1, x0:x1]
    _, bw = cv2.threshold(line, 160, 255, cv2.THRESH_BINARY_INV)
    nlab, _, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    circled = []
    periods = []
    for i in range(1, nlab):
        x, y, ww, hh, area = stats[i]
        if 11 <= ww <= 20 and 10 <= hh <= 20 and 20 <= area <= 95 and abs(int(ww) - int(hh)) <= 6:
            circled.append(int(x))
        if 2 <= ww <= 4 and 2 <= hh <= 4 and 3 <= area <= 8 and y >= line.shape[0] * 0.55:
            periods.append(int(x))
    circled.sort()
    merged = []
    for x in circled:
        if merged and x - merged[-1] < 18:
            continue
        merged.append(x)
    c, p = len(merged), len(periods)
    if c and p and abs(c - p) <= 1:
        return max(c, p)
    if c:
        return c
    if p:
        return p
    return 0


def header_bottom(gray) -> int:
    h, w = gray.shape
    for y in range(100, 230):
        row = gray[y, 80 : w - 90] < 90
        if float(row.mean()) > 0.62:
            return y + 6
    return 176


def footer_top(gray) -> int:
    h, w = gray.shape
    return max(int(h * 0.93), h - 80)


def content_left_x(gray, y0: int, y1: int) -> int:
    """문항 영역의 왼쪽 잉크 시작 x (페이지마다 스캔 여백이 다름)."""
    h, w = gray.shape
    y0 = max(0, y0)
    y1 = min(h, y1)
    if y1 <= y0:
        return 70
    x_hi = min(w, 220)
    band = gray[y0:y1, 20:x_hi]
    col = (band < 170).mean(axis=0)
    for i, v in enumerate(col):
        if v > 0.008 and float(col[max(0, i - 1) : i + 10].mean()) > 0.004:
            return 20 + i
    return 70


def _is_vertical_rule(gray, x: int, y: int, hh: int) -> bool:
    """박스 왼쪽 테두리처럼 위아래로 이어진 선이면 True."""
    h, w = gray.shape
    x0, x1 = max(0, x - 1), min(w, x + 4)
    y0, y1 = max(0, y - 28), min(h, y + hh + 28)
    col = gray[y0:y1, x0:x1]
    if col.size == 0:
        return False
    return float((col < 140).mean()) > 0.42


def find_q_ys(gray, y0: int, y1: int) -> list[int]:
    """왼쪽 여백의 문항 번호(1~20) y좌표만 모은다. 헤더·박스선·보기번호는 제외."""
    if y1 - y0 < 40:
        return []
    left = content_left_x(gray, y0 + 8, y1)
    x0 = max(12, left - 6)
    x1 = min(gray.shape[1] - 8, left + 34)
    strip = gray[y0:y1, x0:x1]
    _, bw = cv2.threshold(strip, 155, 255, cv2.THRESH_BINARY_INV)
    nlab, _, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    raw = []
    for i in range(1, nlab):
        x, y, ww, hh, area = stats[i]
        ax = x0 + int(x)
        ay = y0 + int(y)
        if not (12 <= hh <= 44 and 4 <= ww <= 36 and area >= 24):
            continue
        if ww > hh * 2.2:
            continue
        if ww <= 8 and _is_vertical_rule(gray, ax, ay, hh):
            continue
        if hh >= 38 and _is_vertical_rule(gray, ax, ay, hh):
            continue
        raw.append(ay)
    raw.sort()
    merged: list[int] = []
    for y in raw:
        if merged and y - merged[-1] <= 14:
            continue
        if y1 - y < 22:
            continue
        merged.append(y)
    cleaned: list[int] = []
    for y in merged:
        if cleaned and y - cleaned[-1] < 80:
            continue
        cleaned.append(y)
    return cleaned


def crop_starts_with_number(img) -> bool:
    """크롭 왼쪽 위에 문항 번호가 있으면 True."""
    if img is None or img.size == 0:
        return False
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = g.shape[:2]
    y1 = min(h, 90)
    x1 = min(w, 90)
    strip = g[:y1, :x1]
    _, bw = cv2.threshold(strip, 155, 255, cv2.THRESH_BINARY_INV)
    nlab, _, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    for i in range(1, nlab):
        x, y, ww, hh, area = stats[i]
        if not (12 <= hh <= 52 and 4 <= ww <= 36 and area >= 18 and x <= 62 and y <= 48):
            continue
        if ww > hh * 1.9:
            continue
        # 숫자 1은 가늘다. 박스선만 위아래로 길게 이어진 경우만 제외.
        if ww <= 7 and hh >= 28 and _is_vertical_rule(g, int(x), int(y), hh):
            continue
        return True
    return False


def is_header_only(img) -> bool:
    """과목 뱃지+날짜 헤더(아래 여백 포함)만 있으면 True."""
    if img is None or img.size == 0:
        return True
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = g.shape[:2]
    if crop_starts_with_number(g):
        return False
    if h < 280:
        top_ink = float((g[: min(h, 48)] < 180).mean())
        bot = g[min(h, 48) :]
        bot_ink = float((bot < 180).mean()) if bot.size else 0.0
        if bot_ink < 0.018 and top_ink > 0.008:
            return True
    badge = g[2 : min(h, 78), 2 : min(w, 220)]
    if badge.size and float(badge.mean()) < 175:
        below = g[min(h, 88) :]
        if below.size == 0:
            return True
        if float((below < 180).mean()) < 0.045:
            return True
    if h < 180:
        top = g[: max(1, h // 3)]
        bot = g[h // 2 :]
        if float(top.mean()) < 165 and float(bot.mean()) > 220:
            return True
    return False


def is_weak_crop(img) -> bool:
    """주석 한 줄·보기만 남은 조각."""
    if img is None or img.size == 0:
        return True
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    h, w = g.shape[:2]
    ink = float((g < 200).mean())
    if h < 100:
        return True
    if h < 125 and ink < 0.05:
        return True
    return False


def split_question_starts(gray, y0: int, y1: int, n: int) -> list[int]:
    """문항 영역을 n개로 나눌 시작 y. 번호 검출을 우선하고 부족하면 공백으로 채운다."""
    n = max(1, min(4, n))
    qys = [y for y in find_q_ys(gray, y0, y1) if y < y1 - 20]
    if len(qys) >= n:
        return qys[:n]
    if n >= 2 and len(qys) == 1 and qys[0] > y0 + 140:
        qys = [y0 + 4] + qys
        return qys[:n]
    if n == 1:
        return [qys[0] if qys else y0 + 4]
    # 큰 흰 간격으로 부족한 분할을 채운다
    h, w = gray.shape
    left = content_left_x(gray, y0 + 8, y1)
    ink = (gray[:, max(0, left) : min(w, left + 700)] < 200).mean(axis=1)
    gaps = []
    y = y0 + 80
    while y < y1 - 80:
        if float(ink[y : y + 8].mean()) > 0.01:
            y += 1
            continue
        run = 0
        t = y
        while t < y1 - 40 and float(ink[t : t + 4].mean()) < 0.01:
            run += 1
            t += 1
        if run >= 10:
            after = float(ink[t : min(h, t + 30)].mean())
            if after > 0.015:
                gaps.append((run, t + 2))
        y = t + 1
    gaps.sort(reverse=True)
    extra = [gy for _, gy in gaps if all(abs(gy - q) > 50 for q in qys)]
    qys = sorted(qys + extra[: max(0, n - len(qys))])
    if not qys:
        qys = [y0 + 4]
    if len(qys) < n:
        span = y1 - y0
        qys = [y0 + 4 + int(i * span / n) for i in range(n)]
    return qys[:n]


def trim_crop(img):
    """Trim mostly-white margins but keep a little padding."""
    if img is None or img.size == 0:
        return img
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    mask = g < 245
    ys, xs = np.where(mask)
    if len(ys) < 30:
        return img
    y0, y1 = max(0, ys.min() - 8), min(img.shape[0], ys.max() + 10)
    x0, x1 = max(0, xs.min() - 8), min(img.shape[1], xs.max() + 10)
    return img[y0:y1, x0:x1]


# subject, date, exam_slug, book_start
IRON_EXAMS = [
    ("전기이론", "2021-04-17", "인사혁신처", 8),
    ("전기이론", "2021-06-05", "제1회지방직", 24),
    ("전기이론", "2021-06-05", "제1회서울특별시", 39),
    ("전기이론", "2021-06-05", "제1회서울특별시보훈청추천", 52),
    ("전기이론", "2022-04-02", "인사혁신처", 62),
    ("전기이론", "2022-06-18", "제1회지방직", 75),
    ("전기이론", "2022-06-18", "제2회서울특별시", 89),
    ("전기이론", "2022-06-18", "제2회서울특별시보훈청추천", 100),
    ("전기이론", "2023-04-08", "인사혁신처", 110),
    ("전기이론", "2023-06-10", "제1회지방직", 122),
    ("전기이론", "2023-06-10", "제1회서울특별시보훈청추천", 132),
    ("전기이론", "2023-06-10", "제1회서울특별시", 145),
    ("전기이론", "2024-03-23", "인사혁신처", 161),
    ("전기이론", "2024-06-22", "제1회지방직", 175),
    ("전기이론", "2024-06-22", "제2회서울특별시", 187),
    ("전기이론", "2024-06-22", "제2회서울특별시보훈청추천", 199),
    ("전기이론", "2025-04-05", "국가직", 209),
    ("전기이론", "2025-06-21", "제1회지방직", 223),
    ("전기이론", "2025-06-21", "제1회서울특별시", 239),
    ("전기이론", "2025-06-21", "제1회서울특별시보훈청추천", 253),
    ("전기이론", "2026-04-04", "국가직", 259),
    ("전기이론", "2026-06-20", "제1회지방직", 275),
    ("전기이론", "2026-06-20", "제1회서울특별시", 286),
    ("전기이론", "2026-06-20", "제1회서울특별시보훈청추천", 299),
]
MACHINE_EXAMS = [
    ("전기기기", "2018-03-24", "제1회서울특별시", 2),
    ("전기기기", "2018-04-07", "인사혁신처", 13),
    ("전기기기", "2018-05-19", "제1회지방직", 23),
    ("전기기기", "2018-06-23", "제2회서울특별시", 32),
    ("전기기기", "2019-04-06", "인사혁신처", 41),
    ("전기기기", "2019-06-15", "제1회지방직", 50),
    ("전기기기", "2019-06-15", "제2회서울특별시", 60),
    ("전기기기", "2020-06-13", "제1회지방직제2회서울특별시", 70),
    ("전기기기", "2020-07-11", "인사혁신처", 78),
    ("전기기기", "2021-04-17", "인사혁신처", 89),
    ("전기기기", "2021-06-05", "제1회지방직", 100),
    ("전기기기", "2022-04-02", "인사혁신처", 109),
    ("전기기기", "2022-06-18", "제1회지방직", 118),
    ("전기기기", "2023-04-08", "인사혁신처", 127),
    ("전기기기", "2023-06-10", "제1회지방직", 136),
    ("전기기기", "2024-03-23", "인사혁신처", 146),
    ("전기기기", "2024-06-22", "제1회지방직", 156),
    ("전기기기", "2025-04-05", "국가직", 167),
    ("전기기기", "2025-06-21", "제1회지방직", 178),
    ("전기기기", "2026-04-04", "국가직", 187),
    ("전기기기", "2026-06-20", "제1회지방직", 198),
]


def with_ranges(exams, offset: int, last_pdf: int):
    out = []
    for i, (subj, date, exam, book) in enumerate(exams):
        pdf0 = book + offset
        if i + 1 < len(exams):
            pdf1 = exams[i + 1][3] + offset - 1
        else:
            pdf1 = last_pdf
        out.append((subj, date, exam, pdf0, pdf1))
    return out


def exam_source(date: str, subject: str, exam: str) -> str:
    pretty = (
        exam.replace("제1회", "제1회 ")
        .replace("제2회", "제2회 ")
        .replace("지방직", "지방직 ")
        .replace("서울특별시", "서울특별시 ")
        .replace("보훈청추천", "(보훈청 추천) ")
        .replace("인사혁신처", "인사혁신처 ")
        .replace("국가직", "국가직 ")
    )
    pretty = re.sub(r"\s+", " ", pretty).strip()
    return f"{date} {subject} {pretty}시행"


def finalize_exam_items(items: list[dict], start_qnum: int, subj: str, date: str, exam: str) -> list[dict]:
    """헤더·조각 제거 후 1~20(또는 11~20)으로 번호를 다시 매긴다."""
    want = 20 - start_qnum + 1

    def load_q(it):
        p = HERE / it["q_image"]
        if not p.is_file():
            return None
        return cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)

    kept = []
    for it in items:
        img = load_q(it)
        if img is None:
            continue
        if is_header_only(img):
            continue
        kept.append(it)

    while len(kept) > want:
        drop_i = None
        for i, it in enumerate(kept):
            img = load_q(it)
            if img is not None and not crop_starts_with_number(img):
                drop_i = i
                break
        if drop_i is None:
            heights = []
            for i, it in enumerate(kept):
                img = load_q(it)
                heights.append((img.shape[0] if img is not None else 0, i))
            drop_i = min(heights)[1]
        kept.pop(drop_i)

    if len(kept) < want:
        expanded = []
        for it in kept:
            img = load_q(it)
            g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img is not None else None
            extra = None
            if g is not None and img.shape[0] > 360:
                ys = [y for y in find_q_ys(g, 6, g.shape[0] - 10) if 70 < y < img.shape[0] - 70]
                if len(ys) >= 1:
                    y = ys[0]
                    top, bot = img[: y - 4], img[y - 6 :]
                    if top.shape[0] > 80 and bot.shape[0] > 80 and crop_starts_with_number(bot):
                        extra = (it, top, bot)
            if extra and len(expanded) + (len(kept) - kept.index(it)) < want + 8:
                it_a = dict(it)
                it_b = dict(it)
                stem_a = Path(it["q_image"]).name
                p_a = HERE / it["q_image"]
                p_b = HERE / it["q_image"].replace(".png", "_split.png")
                imwrite_unicode(p_a, extra[1])
                imwrite_unicode(p_b, extra[2])
                it_b["q_image"] = str(Path(it["q_image"]).with_name(p_b.name)).replace("\\", "/")
                if "exam_images" not in it_b["q_image"]:
                    it_b["q_image"] = it["q_image"].replace(".png", "_split.png")
                expanded.append(it_a)
                expanded.append(it_b)
                extra = True
            else:
                expanded.append(it)
            if extra is True and len(expanded) >= want:
                expanded.extend(kept[kept.index(it) + 1 :])
                break
        if len(expanded) > len(kept):
            kept = expanded[:want]

    out = []
    for i, it in enumerate(kept):
        qn = start_qnum + i
        stem = f"{subj}_{date}_{exam}_no{qn:02d}"
        q_rel = f"exam_images/q/q_{stem}.png"
        a_rel = f"exam_images/a/a_{stem}.png"
        old_q = HERE / it["q_image"]
        old_a = HERE / it["a_image"]
        new_q = HERE / q_rel
        new_a = HERE / a_rel
        if old_q.resolve() != new_q.resolve() and old_q.is_file():
            new_q.write_bytes(old_q.read_bytes())
        if old_a.resolve() != new_a.resolve() and old_a.is_file():
            new_a.write_bytes(old_a.read_bytes())
        it = dict(it)
        it["q_num"] = qn
        it["q_image"] = q_rel
        it["a_image"] = a_rel
        it["orig"] = f"q_{stem}.png"
        it["q"] = f"img::q_{stem}.png"
        out.append(it)
    return out


def extract_exam(subj, date, exam, pdf0, pdf1, start_qnum: int = 1, first_page_skip: int = 0) -> list[dict]:
    items = []
    qnum = start_qnum - 1
    first_content = True
    for pn in range(pdf0, pdf1 + 1):
        gray = load_gray(pn)
        bgr = load_bgr(pn)
        if gray is None or bgr is None:
            continue
        h, w = gray.shape
        ay, score, ax = find_answer(gray)
        if score < ANSWER_SCORE_MIN:
            continue
        hb = header_bottom(gray)
        ft = footer_top(gray)
        q_top = min(max(hb, 120), ay - 30)
        if first_content and first_page_skip:
            q_top = min(q_top + first_page_skip, ay - 80)
        first_content = False
        n_circ = answer_line_qcount(gray, ay, ax)
        n_ys = len([y for y in find_q_ys(gray, q_top, ay - 8) if y < ay - 20])
        n_page = max(n_circ, n_ys, 1)
        n_page = min(n_page, 4)
        qys = split_question_starts(gray, q_top, ay - 8, n_page)
        if qys:
            y_a = max(q_top - 4, qys[0] - 8)
            y_b = qys[1] - 4 if len(qys) > 1 else ay - 4
            probe = trim_crop(bgr[y_a:y_b, max(8, content_left_x(gray, q_top + 8, ay - 8) - 22) : w - 40])
            if is_header_only(probe):
                nxt = qys[1] - 8 if len(qys) > 1 else min(qys[0] + 90, ay - 90)
                q_top = min(max(nxt, q_top + 40), ay - 90)
                qys = split_question_starts(gray, q_top, ay - 8, n_page)
        left = content_left_x(gray, q_top + 8, ay - 8)
        x_q0 = max(8, left - 22)
        a_y0 = max(0, ay - 6)
        a_y1 = min(h, ft)
        ans_img = trim_crop(bgr[a_y0:a_y1, x_q0 : w - 40])
        for i, y in enumerate(qys):
            y0 = max(q_top - 4, y - 8)
            y1 = qys[i + 1] - 4 if i + 1 < len(qys) else ay - 4
            if y1 - y0 < 50:
                continue
            q_img = trim_crop(bgr[y0:y1, x_q0 : w - 40])
            if q_img is None or q_img.size == 0 or q_img.shape[1] < 160:
                continue
            if is_header_only(q_img) and i == 0 and len(qys) > n_page:
                continue
            qnum += 1
            stem = f"{subj}_{date}_{exam}_no{qnum:02d}"
            q_rel = f"exam_images/q/q_{stem}.png"
            a_rel = f"exam_images/a/a_{stem}.png"
            imwrite_unicode(HERE / q_rel, q_img)
            imwrite_unicode(HERE / a_rel, ans_img if ans_img is not None and ans_img.size else q_img)
            items.append(
                {
                    "source": exam_source(date, subj, exam),
                    "q": f"img::q_{stem}.png",
                    "choices": ["①", "②", "③", "④"],
                    "answer": -1,
                    "explain": "",
                    "visual": "",
                    "caption": "",
                    "q_image": q_rel,
                    "a_image": a_rel,
                    "image_mode": True,
                    "q_num": qnum,
                    "subject": subj,
                    "orig": f"q_{stem}.png",
                    "_pdf_page": pn,
                }
            )
    return finalize_exam_items(items, start_qnum, subj, date, exam)


def orig_key(orig: str) -> tuple[str, str, str, int] | None:
    s = Path(orig).stem
    s = re.sub(r"_v\d+$", "", s)
    if s.startswith("q_"):
        s = s[2:]
    m = re.match(r"^(전기기기|전기이론)_(\d{4}-\d{2}-\d{2})_(.+)_no(\d+)$", s)
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3).replace(" ", ""), int(m.group(4))


def normalize_exam(name: str) -> str:
    n = name.replace(" ", "").replace("(", "").replace(")", "")
    n = n.replace("보훈청추천", "보훈청추천")
    return n


def is_toc_item(key: tuple[str, str, str, int], toc_set: set) -> bool:
    subj, date, exam, _q = key
    exam = normalize_exam(exam)
    return (subj, date, exam) in toc_set or any(
        s == subj and d == date and (exam in e or e in exam)
        for s, d, e in toc_set
    )


def max_q_index(questions: list[dict]) -> int:
    mx = 0
    for q in questions:
        m = re.search(r"q(\d{4})", str(q.get("q") or ""))
        if m:
            mx = max(mx, int(m.group(1)))
        rel = q.get("q_image") or ""
        m = re.search(r"q(\d{4})\.", rel)
        if m:
            mx = max(mx, int(m.group(1)))
    return mx


def main() -> None:
    global ANSWER_TMPL
    ANSWER_TMPL = make_answer_tmpl()
    Q_DIR.mkdir(parents=True, exist_ok=True)
    A_DIR.mkdir(parents=True, exist_ok=True)

    exams = with_ranges(IRON_EXAMS, IRON_OFFSET, IRON_PDF_END) + with_ranges(
        MACHINE_EXAMS, MACHINE_OFFSET, MACHINE_PDF_END
    )
    extracted: list[dict] = []
    report = []
    by_key: dict[tuple, list[dict]] = {}
    for i, (subj, date, exam, pdf0, pdf1) in enumerate(exams, 1):
        short_bohun = "보훈" in exam and (pdf1 - pdf0 + 1) <= 7
        start = 11 if short_bohun else 1
        skip = 180 if short_bohun else 0
        items = extract_exam(subj, date, exam, pdf0, pdf1, start_qnum=start, first_page_skip=skip)
        by_key[(subj, date, exam)] = items
        extracted.extend(items)
        report.append(
            {
                "subject": subj,
                "date": date,
                "exam": exam,
                "pdf": [pdf0, pdf1],
                "count": len(items),
                "nums": [x["q_num"] for x in items],
                "bohun_partial": short_bohun,
            }
        )
        print(f"[{i:02d}/{len(exams)}] {subj} {date} {exam}  {len(items)}문항  (pdf {pdf0}-{pdf1})")

    # 보훈 1~10번은 서울시와 동일 → 서울시 이미지를 그대로 붙인다
    filled = 0
    for (subj, date, exam), items in list(by_key.items()):
        if "보훈" not in exam:
            continue
        if items and min(x["q_num"] for x in items) == 1:
            continue
        seoul_key = None
        for (s, d, e) in by_key:
            if s == subj and d == date and "서울" in e and "보훈" not in e:
                seoul_key = (s, d, e)
                break
        if seoul_key is None:
            continue
        clones = []
        for it in by_key[seoul_key]:
            if it["q_num"] > 10:
                continue
            n = dict(it)
            n.pop("_pdf_page", None)
            n["source"] = exam_source(date, subj, exam)
            stem = f"{subj}_{date}_{exam}_no{it['q_num']:02d}"
            n["orig"] = f"q_{stem}.png"
            n["q"] = f"img::q_{stem}.png"
            clones.append(n)
        if clones:
            by_key[(subj, date, exam)] = clones + items
            filled += len(clones)

    extracted = []
    for r in report:
        key = (r["subject"], r["date"], r["exam"])
        items = by_key.get(key, [])
        r["count"] = len(items)
        r["nums"] = [x["q_num"] for x in items]
        extracted.extend(items)

    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    old = data.get("questions") or []
    toc_set = {(s, d, normalize_exam(e)) for s, d, e, *_ in exams}

    legacy = []
    replaced = 0
    for q in old:
        key = orig_key(q.get("orig") or "")
        if key and is_toc_item(key, toc_set):
            replaced += 1
            continue
        legacy.append(q)

    # drop extractor-only field
    clean = []
    for it in extracted:
        it = dict(it)
        it.pop("_pdf_page", None)
        clean.append(it)

    merged = legacy + clean
    data["questions"] = merged
    JSON_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    used = set()
    for q in merged:
        for key in ("q_image", "a_image"):
            rel = q.get(key) or ""
            if rel:
                used.add(str(HERE / rel).lower())
    removed = 0
    for folder in (Q_DIR, A_DIR):
        for p in folder.glob("*.png"):
            name = p.name
            if not any(s in name for s, _, _, _ in IRON_EXAMS + MACHINE_EXAMS):
                continue
            if str(p).lower() not in used:
                p.unlink(missing_ok=True)
                removed += 1
    if removed:
        print(f"removed unused TOC crops: {removed}")

    short = [r for r in report if r["count"] != 20]
    print()
    print(f"extracted {len(extracted)} from PDF, kept legacy {len(legacy)}, replaced {replaced}")
    print(f"quiz bank total {len(merged)}")
    print(f"exams not 20문항: {len(short)} / {len(report)}")
    for r in short:
        print(f"  {r['count']:2d}  {r['subject']} {r['date']} {r['exam']}")


if __name__ == "__main__":
    main()
