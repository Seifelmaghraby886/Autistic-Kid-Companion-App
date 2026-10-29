#!/usr/bin/env bash
# One-time Raspberry Pi setup for Wanees.
#   Intended target: Raspberry Pi 5 (8 GB), Raspberry Pi OS 64-bit (Bookworm).
#   A 64-bit OS is required (PySide6 has no 32-bit ARM wheels).
#   Run from the app folder:   bash deploy/setup_pi.sh
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$APP_DIR"

echo "== 1/5 System packages =="
sudo apt-get update
sudo apt-get install -y \
    python3-venv python3-dev build-essential \
    portaudio19-dev libasound2-dev \
    espeak-ng \
    fonts-noto-color-emoji fonts-noto-core \
    libgl1 libxcb-cursor0 v4l-utils

echo "== 2/5 Python environment =="
python3 -m venv .venv
.venv/bin/pip install --upgrade pip wheel
# TensorFlow is installed separately: it is large and only needed for the
# on-demand camera emotion screens, so a failure must not block the app.
grep -viE '^(tensorflow|pyinstaller)' requirements.txt > /tmp/wanees_reqs.txt
.venv/bin/pip install -r /tmp/wanees_reqs.txt
.venv/bin/pip install tensorflow \
    || echo "!! TensorFlow did not install — the app runs, camera emotion screens will be limited"

echo "== 3/5 Pi performance settings =="
# Animated backgrounds are costly on the Pi GPU/CPU — start static.
.venv/bin/python - <<'EOF'
import json
p = "config/app_config.json"
cfg = json.load(open(p, encoding="utf-8"))
cfg["reduce_motion"] = True
cfg["kiosk_mode"] = True
cfg["auto_start_child"] = True
json.dump(cfg, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("config updated: reduce_motion, kiosk_mode, auto_start_child = true")
EOF

echo "== 4/5 Launcher + autostart on boot =="
chmod +x run_aria.sh
mkdir -p "$HOME/.config/autostart"
sed "s|__APP_DIR__|$APP_DIR|g" deploy/wanees.desktop > "$HOME/.config/autostart/wanees.desktop"

echo "== 5/5 Hardware check =="
echo "-- cameras:"; v4l2-ctl --list-devices 2>/dev/null || echo "   none found"
echo "-- microphones:"; arecord -l 2>/dev/null || echo "   none found"
.venv/bin/python -c "import PySide6, cv2, pygame; print('core imports OK')"

echo
echo "Done. Reboot and Wanees opens by itself:   sudo reboot"
echo "Run it now manually with:                  ./run_aria.sh"
