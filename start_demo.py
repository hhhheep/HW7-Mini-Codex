from __future__ import annotations

import subprocess
import sys
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "outputs" / "streamlit_demo.log"


def main() -> int:
    port = 8501
    if _is_live(port):
        print(f"already running: http://localhost:{port}")
        return 0

    LOG_PATH.parent.mkdir(exist_ok=True)
    log = LOG_PATH.open("a", encoding="utf-8")
    executable = _launcher_executable()
    command = [
        str(executable),
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--browser.gatherUsageStats",
        "false",
    ]
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    for _ in range(20):
        time.sleep(0.5)
        if _is_live(port):
            print(f"started: http://localhost:{port}")
            print(f"pid: {process.pid}")
            print(f"log: {LOG_PATH}")
            return 0
        if process.poll() is not None:
            break
    print(f"failed to start; see {LOG_PATH}")
    return 1


def _is_live(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://localhost:{port}", timeout=1) as response:
            return response.status == 200
    except Exception:
        return False


def _launcher_executable() -> Path:
    executable = Path(sys.executable)
    if sys.platform == "win32":
        pythonw = executable.with_name("pythonw.exe")
        if pythonw.exists():
            return pythonw
    return executable


if __name__ == "__main__":
    raise SystemExit(main())
