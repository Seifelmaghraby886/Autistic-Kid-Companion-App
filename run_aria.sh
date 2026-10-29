#!/usr/bin/env bash
# Launch Wanees on Linux / Raspberry Pi (counterpart of run_aria.bat).
cd "$(dirname "$0")"
if [ -x .venv/bin/python ]; then
    exec .venv/bin/python main.py
fi
exec python3 main.py
