from __future__ import annotations

import sys
from pathlib import Path

import app_paths


def test_source_mode_uses_repo_questions() -> None:
    path = app_paths.resolve_questions_path()
    assert path.is_file(), path
    assert path.name == "questions.json"
    assert path.parent == Path(__file__).resolve().parent


def test_frozen_prefers_sidecar_then_bundle(tmp_path: Path, monkeypatch) -> None:
    exe_dir = tmp_path / "app"
    bundle_dir = tmp_path / "meipass"
    exe_dir.mkdir()
    bundle_dir.mkdir()
    bundled = bundle_dir / "questions.json"
    bundled.write_text("{}", encoding="utf-8")

    fake_exe = exe_dir / "QuizAlert.exe"
    fake_exe.write_bytes(b"")

    monkeypatch.setattr(app_paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(app_paths.sys, "executable", str(fake_exe))
    monkeypatch.setattr(app_paths.sys, "_MEIPASS", str(bundle_dir), raising=False)

    assert app_paths.resolve_questions_path() == bundled

    sidecar = exe_dir / "questions.json"
    sidecar.write_text('{"questions":[]}', encoding="utf-8")
    assert app_paths.resolve_questions_path() == sidecar


if __name__ == "__main__":
    import traceback

    class FakeMonkey:
        def setattr(self, obj, name, value, raising=True):
            setattr(obj, name, value)

    failed = 0
    try:
        test_source_mode_uses_repo_questions()
        print("ok source")
    except Exception:
        failed += 1
        traceback.print_exc()

    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        try:
            test_frozen_prefers_sidecar_then_bundle(Path(raw), FakeMonkey())
            print("ok frozen")
        except Exception:
            failed += 1
            traceback.print_exc()

    sys.exit(failed)
