"""Cross-platform camera opener.

Windows needs the DirectShow backend for fast, reliable opens; on Linux
(Raspberry Pi) that backend doesn't exist and passing it makes every open
fail, so V4L2 is used instead. If the preferred backend can't open the
device, OpenCV's default backend gets one more try.
"""
import sys

import cv2


def _preferred_backend():
    if sys.platform.startswith("win"):
        return cv2.CAP_DSHOW
    if sys.platform.startswith("linux"):
        return cv2.CAP_V4L2
    return cv2.CAP_ANY


def open_camera(index=0):
    """Return an opened cv2.VideoCapture, or an unopened one if no backend works."""
    cap = cv2.VideoCapture(index, _preferred_backend())
    if cap.isOpened():
        return cap
    cap.release()
    return cv2.VideoCapture(index)
