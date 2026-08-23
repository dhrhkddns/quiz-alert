"""문항별 상세 해설(공식·풀이) 생성."""

from __future__ import annotations

import re
from typing import Iterable

STUB_MARKERS = ("0gichul", "comcbt", "번 (0gichul)", "번 (comcbt)")

# 용어별 추가 공식 (정의에 없는 핵심식)
TERM_FORMULAS: dict[str, list[str]] = {
    "쿨롱의 법칙": ["F = q₁q₂ / (4πεr²)", "ε = ε₀εᵣ"],
    "가우스 법칙": ["∮D·dS = Q_enclosed", "D = εE"],
    "옴의 법칙": ["V = IR", "I = V/R", "R = V/I", "P = VI = I²R = V²/R"],
    "키르히호프 전류법칙(KCL)": ["ΣI_in = ΣI_out (노드)", "ΣI = 0 (절점)"],
    "키르히호프 전압법칙(KVL)": ["ΣV = 0 (폐회로)", "전압강하의 대수합 = 0"],
    "테브난 정리": ["Vth = 개방단자전압", "Rth = 독립원=0일 때 단자간 저항", "V = Vth − I·Rth"],
    "노orton 정리": ["In = 단락전류", "Rn = Rth", "I = In − V/Rn"],
    "최대전력 전달정리": ["RL = Rth 일 때 Pmax", "Pmax = Vth² / (4Rth)"],
    "정전용량": ["C = Q/V", "C = εA/d"],
    "커패시터(축전기)": ["Q = CV", "W = (1/2)CV² = Q²/(2C)"],
    "직렬결합": ["1/Ceq = 1/C₁ + 1/C₂ + …"],
    "병렬결합": ["Ceq = C₁ + C₂ + …"],
    "전기에너지": ["W = (1/2)CV²", "W = Q²/(2C)"],
    "유효전력": ["P = VI cosθ", "P = I²R (저항)"],
    "무효전력": ["Q = VI sinθ", "단위: var"],
    "피상전력": ["S = VI", "S = √(P²+Q²)", "단위: VA"],
    "역률": ["cosθ = P/S", "sinθ = Q/S", "tanθ = Q/P"],
    "임피던스": ["Z = R + jX", "|Z| = √(R²+X²)"],
    "유도리액턴스": ["XL = 2πfL = ωL"],
    "용량리액턴스": ["XC = 1/(2πfC) = 1/(ωC)"],
    "공진주파수": ["f₀ = 1/(2π√(LC))", "ω₀ = 1/√(LC)"],
    "직렬공진": ["XL = XC", "Z = R (최소)"],
    "병렬공진": ["XL = XC", "Z (최대)"],
    "패러데이 전자유도 법칙": ["e = −N dΦ/dt", "Φ = BA"],
    "자기유도": ["e = −L di/dt", "W = (1/2)LI²"],
    "인덕턴스": ["V = L di/dt", "W = (1/2)LI²"],
    "상호인덕턴스": ["M = k√(L₁L₂)", "e₂ = −M di₁/dt"],
    "앙페르의 법칙": ["H = NI/l (솔레노이드)", "B = μH"],
    "실효값(RMS)": ["Vrms = Vm/√2 (정현파)", "Irms = √(평균 i²)"],
    "슬립": ["s = (Ns−N)/Ns", "Ns = 120f/P"],
    "동기속도": ["Ns = 120f/P [rpm]"],
    "변압기": ["V₁/V₂ = N₁/N₂", "I₁/I₂ = N₂/N₁", "S₁ = S₂"],
    "유기기전력": ["E = 4.44 f N Φ", "E = PZΦN/(60a) (DC)"],
    "SCR": ["게이트 턴온, 전류 0에서 턴오프"],
    "IGBT": ["MOSFET 게이트 + BJT 출력"],
    "GTO": ["게이트로 턴온·턴오프"],
}

TOPIC_FORMULAS: list[tuple[tuple[str, ...], list[str]]] = [
    (("3상", "평형"), ["P = √3 VL IL cosθ", "S = √3 VL IL", "Y결선: Vp=VL/√3, Ip=IL", "△결선: Vp=VL, Ip=IL/√3"]),
    (("역률", "cos"), ["cosθ = P/S", "P = VI cosθ", "Q = VI sinθ", "S = VI"]),
    (("커패시터", "정전용량", "축전"), ["Q = CV", "C = εA/d", "W = (1/2)CV²", "XC = 1/(ωC)"]),
    (("인덕터", "인덕턴스"), ["V = L di/dt", "XL = ωL", "W = (1/2)LI²"]),
    (("RLC", "공진"), ["f₀ = 1/(2π√(LC))", "XL = XC", "Q = ωL/R"]),
    (("테브난", "등가"), ["Vth: 개방전압", "Rth: 독립원=0 등가저항", "RL=Rth → 최대전력"]),
    (("노orton",), ["In: 단락전류", "Rn = Rth"]),
    (("직류전동기", "전기자"), ["E = V − IaRa", "T ∝ ΦIa", "P = EIa"]),
    (("유도전동기", "슬립"), ["s = (Ns−N)/Ns", "Ns = 120f/P", "T ∝ s (근처)"]),
    (("변압기", "변압"), ["V₁/V₂ = N₁/N₂", "E = 4.44fNΦBmA", "ΔV% = (Vnr−V)/V×100"]),
    (("동기",), ["Ns = 120f/P", "f = PN/120"]),
    (("평행", "도선"), ["F/l = μ₀I₁I₂/(2πd)", "같은 방향: 흡인, 반대: 반발"]),
    (("쿨롱", "전하"), ["F = q₁q₂/(4πεr²)"]),
    (("전계", "전위"), ["E = −∇V", "V = −∫E·dl", "W = qΔV"]),
    (("자속", "자계"), ["Φ = BA", "B = μH", "F = BIl"]),
    (("실효", "RMS"), ["Vrms = Vm/√2", "P = Vrms Irms cosθ"]),
    (("임피던스", "리액턴스"), ["Z = R + jX", "Z_R=R", "Z_L=jωL", "Z_C=−j/(ωC)"]),
]


def is_stub_explain(explain: str) -> bool:
    ex = explain.strip()
    if not ex:
        return True
    return any(m in ex for m in STUB_MARKERS) or bool(re.fullmatch(r".+\d+번\s*\([^)]+\)", ex))


def needs_enrich(item: dict) -> bool:
    ex = item.get("explain", "")
    if "【정답】" in ex and len(ex) >= 150:
        return False
    if is_stub_explain(ex):
        return True
    if item.get("source", "").startswith("용어정의"):
        return "【정답】" not in ex
    if len(ex) < 150:
        return True
    return False


def _extract_paren_formulas(text: str) -> list[str]:
    found: list[str] = []
    for m in re.finditer(r"\(([^)]*[=\+\-\*/×÷√][^)]*)\)", text):
        s = m.group(1).strip()
        if 2 < len(s) < 80:
            found.append(s)
    return found


def formulas_for_question(text: str) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for keys, formulas in TOPIC_FORMULAS:
        if any(k in text for k in keys):
            for f in formulas:
                if f not in seen:
                    seen.add(f)
                    out.append(f)
    for f in _extract_paren_formulas(text):
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out[:8]


def _fmt_formulas(formulas: Iterable[str]) -> str:
    lines = list(formulas)
    if not lines:
        return "• (개념·서술형 — 아래 정의·논리로 풉니다)"
    return "\n".join(f"• {f}" for f in lines)


def _fmt_choices(choices: list[str], answer: int) -> str:
    lines = []
    for i, c in enumerate(choices):
        mark = " ← 정답" if i == answer else ""
        lines.append(f"  {i + 1}. {c}{mark}")
    return "\n".join(lines)


def build_term_explain(term: str, definition: str, choices: list[str], answer: int) -> str:
    correct = choices[answer]
    formulas = list(TERM_FORMULAS.get(term, []))
    formulas.extend(_extract_paren_formulas(definition))
    # dedupe
    uniq: list[str] = []
    seen: set[str] = set()
    for f in formulas:
        if f not in seen:
            seen.add(f)
            uniq.append(f)

    wrong = [choices[i] for i in range(len(choices)) if i != answer]
    return (
        f"【용어】 {term}\n\n"
        f"【정답】 {answer + 1}번\n{correct}\n\n"
        f"【정의】\n{definition}\n\n"
        f"【핵심 공식】\n{_fmt_formulas(uniq)}\n\n"
        f"【풀이】\n"
        f"「{term}」의 설명을 묻는 용어 문제입니다.\n"
        f"정답 {answer + 1}번은 교재·기출 정의와 일치합니다.\n"
        f"나머지 보기({len(wrong)}개)는 다른 용어의 정의이므로 제외합니다.\n\n"
        f"【보기 검토】\n{_fmt_choices(choices, answer)}"
    )


def build_generic_explain(item: dict, extra_steps: str = "") -> str:
    q = item["q"]
    choices = item["choices"]
    answer = int(item["answer"])
    correct = choices[answer]
    formulas = formulas_for_question(q)
    old = item.get("explain", "").strip()
    steps = extra_steps.strip()
    if not steps and old and not is_stub_explain(old):
        steps = (
            f"기존 해설 요약:\n{old}\n\n"
            f"→ 위 계산·논리를 단계별로 풀면 정답 {answer + 1}번 「{correct}」에 도달합니다."
        )

    body = (
        f"【문제 요지】\n{q}\n\n"
        f"【정답】 {answer + 1}번\n{correct}\n\n"
        f"【풀이에 쓰는 공식】\n{_fmt_formulas(formulas)}\n\n"
        f"【풀이】\n"
    )
    if steps:
        body += steps + "\n\n"
    else:
        body += (
            f"1) 문제에서 요구하는 물리량·개념을 확인합니다.\n"
            f"2) 위 공식에 주어진 값을 대입하거나, 개념적으로 옳은 서술을 고릅니다.\n"
            f"3) 계산·논리 결과가 {answer + 1}번 「{correct}」와 일치합니다.\n\n"
        )
    body += f"【보기】\n{_fmt_choices(choices, answer)}"
    return body.strip()


def parse_term_from_question(q: str) -> str | None:
    m = re.search(r"「(.+?)」", q)
    return m.group(1) if m else None


def lookup_term_definition(term: str) -> str | None:
    try:
        from term_bank import TERM_DEFINITIONS
    except ImportError:
        return None
    for t, _subj, definition in TERM_DEFINITIONS:
        if t == term:
            return definition
    return None
