#!/usr/bin/env python3
"""
macOS launchd servis kurulum scripti.
Kullanım:
  python3 setup_service.py install    → servisi kur ve başlat
  python3 setup_service.py uninstall  → servisi durdur ve kaldır
  python3 setup_service.py status     → servis durumunu göster
  python3 setup_service.py logs       → son logları göster
"""

import sys
import os
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
VENV_PYTHON = PROJECT_DIR / "venv" / "bin" / "python3"
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
PLIST_NAME = "com.discountracking.app"
PLIST_PATH = LAUNCH_AGENTS_DIR / f"{PLIST_NAME}.plist"
LOG_DIR = PROJECT_DIR / "logs"


def plist_content():
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>

    <key>ProgramArguments</key>
    <array>
        <string>{VENV_PYTHON}</string>
        <string>{PROJECT_DIR / "app.py"}</string>
    </array>

    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{LOG_DIR / "app.log"}</string>

    <key>StandardErrorPath</key>
    <string>{LOG_DIR / "app_error.log"}</string>

    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
"""


def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"HATA: {result.stderr.strip()}")
    return result


def install():
    if not VENV_PYTHON.exists():
        print("HATA: venv bulunamadı. Önce 'python3 -m venv venv && venv/bin/pip install -r requirements.txt' çalıştırın.")
        sys.exit(1)

    LOG_DIR.mkdir(exist_ok=True)
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)

    # Zaten yüklüyse önce kaldır
    if PLIST_PATH.exists():
        run(f"launchctl unload {PLIST_PATH}", check=False)

    PLIST_PATH.write_text(plist_content())
    result = run(f"launchctl load {PLIST_PATH}")

    if result.returncode == 0:
        print("✅ Servis kuruldu ve başlatıldı!")
        print(f"   Web arayüzü: http://localhost:8081")
        print(f"   Loglar:      {LOG_DIR}/app.log")
        print(f"\n   Bilgisayar her açıldığında otomatik başlayacak.")
        print(f"   Durdurmak için: python3 setup_service.py uninstall")
    else:
        print("HATA: Servis başlatılamadı.")


def uninstall():
    if not PLIST_PATH.exists():
        print("Servis zaten kurulu değil.")
        return
    run(f"launchctl unload {PLIST_PATH}", check=False)
    PLIST_PATH.unlink()
    print("✅ Servis durduruldu ve kaldırıldı.")


def status():
    result = run(f"launchctl list | grep {PLIST_NAME}", check=False)
    if result.stdout.strip():
        parts = result.stdout.strip().split()
        pid = parts[0] if parts[0] != "-" else None
        if pid:
            print(f"✅ Servis ÇALIŞIYOR (PID: {pid})")
        else:
            last_exit = parts[1] if len(parts) > 1 else "?"
            print(f"⚠️  Servis kayıtlı ama çalışmıyor (son çıkış kodu: {last_exit})")
    else:
        print("❌ Servis kurulu değil.")

    log = LOG_DIR / "app.log"
    if log.exists():
        lines = log.read_text().strip().splitlines()
        if lines:
            print(f"\nSon log satırı: {lines[-1]}")


def logs():
    log = LOG_DIR / "app.log"
    err = LOG_DIR / "app_error.log"
    if log.exists():
        print("=== app.log (son 30 satır) ===")
        lines = log.read_text().strip().splitlines()
        print("\n".join(lines[-30:]))
    if err.exists() and err.stat().st_size > 0:
        print("\n=== app_error.log (son 20 satır) ===")
        lines = err.read_text().strip().splitlines()
        print("\n".join(lines[-20:]))


COMMANDS = {"install": install, "uninstall": uninstall, "status": status, "logs": logs}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    COMMANDS[cmd]()
