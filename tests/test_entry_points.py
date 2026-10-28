"""Offscreen entry-point smoke tests; automatically exit the real Qt event loop."""
import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("entry", ["main.py", "app.py"])
def test_entry_point_shows_window_and_enters_event_loop(entry, tmp_path):
    root = Path(__file__).resolve().parents[1]
    # Only the event-loop exit is instrumented. The entry point constructs and
    # shows its actual window; using another cwd catches relative-import mistakes.
    script = r'''
import runpy
import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
sys.path.insert(0, sys.argv[1])
original_exec = QApplication.exec
def bounded_exec():
    app = QApplication.instance()
    windows = [w for w in app.topLevelWidgets() if w.isVisible() and w.windowTitle().startswith("ECAS")]
    assert len(windows) == 1, "No visible ECAS window before event loop"
    QTimer.singleShot(100, app.quit)
    code = original_exec()
    print("ECAS_WINDOW_AND_EVENT_LOOP_OK", flush=True)
    return code
QApplication.exec = staticmethod(bounded_exec)
runpy.run_path(sys.argv[2], run_name="__main__")
'''
    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run([sys.executable, "-I", "-B", "-c", script,
                             str(root), str(root / entry)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ECAS_WINDOW_AND_EVENT_LOOP_OK" in result.stdout
