#!/usr/bin/env python3
"""questions.json 해설을 검증·보강한다."""

from __future__ import annotations

import json
import re
from pathlib import Path

from explain_builder import (
    build_generic_explain,
    build_term_explain,
    is_stub_explain,
    lookup_term_definition,
    needs_enrich,
    parse_term_from_question,
)

HERE = Path(__file__).resolve().parent


def _load_web_explains() -> dict[str, str]:
    try:
        from web_explains import WEB_EXPLAINS
        return WEB_EXPLAINS
    except ImportError:
        return {}


def enrich_item(item: dict, web: dict[str, str]) -> dict:
    q = item["q"].strip()
    if not needs_enrich(item) and not is_stub_explain(item.get("explain", "")):
        return item

    term = parse_term_from_question(q)
    if term:
        definition = lookup_term_definition(term)
        if definition:
            item = dict(item)
            item["explain"] = build_term_explain(
                term, definition, item["choices"], int(item["answer"])
            )
            item["caption"] = f"{term} — {definition[:60]}"
            return item

    if q in web:
        steps = web[q]
        item = dict(item)
        item["explain"] = build_generic_explain(item, extra_steps=steps)
        item["caption"] = steps.split("\n")[0][:80]
        return item

    old = item.get("explain", "").strip()
    if old and not is_stub_explain(old):
        extra = old
    else:
        extra = _auto_steps(item)
    item = dict(item)
    item["explain"] = build_generic_explain(item, extra_steps=extra)
    first = item["explain"].split("\n")[2] if item["explain"] else q[:40]
    item["caption"] = re.sub(r"^【[^】]+】\s*", "", first)[:80]
    return item


def _auto_steps(item: dict) -> str:
    """기존 짧은 해설·보기만으로 보강."""
    q = item["q"]
    choices = item["choices"]
    ans = int(item["answer"])
    correct = choices[ans]
    old = item.get("explain", "").strip()
    lines = []
    if old and not is_stub_explain(old):
        lines.append(old)
    lines.append(f"정답 {ans + 1}번 「{correct}」이(가) 문제 조건·공식에 부합합니다.")
    if "옳지 않은" in q or "틀린" in q or "아닌" in q:
        lines.append("「옳지 않은/아닌 것」 유형이므로, 틀린 서술 1개를 고릅니다.")
    return "\n".join(lines)


def main() -> None:
    path = HERE / "questions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    web = _load_web_explains()
    questions = data.get("questions") or []
    enriched = 0
    for i, item in enumerate(questions):
        before = item.get("explain", "")
        new_item = enrich_item(item, web)
        if new_item.get("explain") != before:
            enriched += 1
        questions[i] = new_item
    data["questions"] = questions
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"enriched {enriched}/{len(questions)} (web overrides: {len(web)})")


if __name__ == "__main__":
    main()
