"""
ARIA Face ID — optional parent feature (off by default)
=======================================================
Recognises which enrolled child is in front of the camera so ARIA OS can
auto-load their profile at startup.

Dependency-free by design:
  * if OpenCV's contrib 'face' module is installed -> uses the LBPH
    recogniser (most reliable);
  * otherwise -> an ORB feature-matching fallback that needs only the base
    opencv-python that ships with ARIA.

For the most reliable recognition, install the contrib build once:
    pip install opencv-contrib-python
ARIA picks it up automatically — no code change needed.

Enrollment images live in  models/faces/<child_id>/.
"""

from pathlib import Path

import cv2
import numpy as np


_FACES_DIR = Path(__file__).parent.parent / "models" / "faces"
_FACE_SIZE = (200, 200)
_ORB_THRESHOLD = 14        # min "good" ORB matches to accept an identity
_LBPH_MAX_DISTANCE = 72.0  # LBPH distance: lower = better; reject above this


def lbph_available() -> bool:
    """True if the OpenCV contrib LBPH face recogniser is installed."""
    try:
        return hasattr(cv2, "face") and hasattr(cv2.face, "LBPHFaceRecognizer_create")
    except Exception:
        return False


def _prep(face):
    """Normalise a face crop -> equalised grayscale at a fixed size."""
    try:
        if face is None or getattr(face, "size", 0) == 0:
            return None
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY) if face.ndim == 3 else face
        gray = cv2.resize(gray, _FACE_SIZE)
        return cv2.equalizeHist(gray)
    except Exception:
        return None


class FaceRecognizer:
    """Enrols children's faces and identifies who is at the camera."""

    def __init__(self):
        try:
            _FACES_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        self._backend = "lbph" if lbph_available() else "orb"
        self._orb = cv2.ORB_create(nfeatures=500)
        self._matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
        self._lbph = None
        self._lbph_labels = {}     # numeric label -> child_id
        self._orb_cache = {}       # child_id -> [descriptors, ...]
        self._load()

    @property
    def backend(self) -> str:
        return self._backend

    # ── enrollment ───────────────────────────────────────────────────
    def enroll(self, child_id, face_crops) -> int:
        """Save a set of face crops (BGR images) for a child. Returns count saved."""
        cdir = _FACES_DIR / str(child_id)
        cdir.mkdir(parents=True, exist_ok=True)
        start = len(list(cdir.glob("face_*.png")))
        saved = 0
        for i, crop in enumerate(face_crops):
            g = _prep(crop)
            if g is None:
                continue
            try:
                cv2.imwrite(str(cdir / f"face_{start + i:03d}.png"), g)
                saved += 1
            except Exception:
                pass
        self._load()
        return saved

    def clear(self, child_id):
        """Remove all enrolled faces for a child."""
        cdir = _FACES_DIR / str(child_id)
        if cdir.exists():
            for f in cdir.glob("*.png"):
                try:
                    f.unlink()
                except Exception:
                    pass
        self._load()

    def enrolled_children(self):
        out = []
        if _FACES_DIR.exists():
            for d in _FACES_DIR.iterdir():
                if d.is_dir() and any(d.glob("face_*.png")):
                    try:
                        out.append(int(d.name))
                    except ValueError:
                        pass
        return out

    def sample_count(self, child_id) -> int:
        cdir = _FACES_DIR / str(child_id)
        return len(list(cdir.glob("face_*.png"))) if cdir.exists() else 0

    def has_enrollment(self) -> bool:
        return len(self.enrolled_children()) > 0

    # ── (re)load the recogniser from disk ────────────────────────────
    def _load(self):
        self._orb_cache.clear()
        self._lbph_labels.clear()
        self._lbph = None
        children = self.enrolled_children()
        if not children:
            return
        if self._backend == "lbph":
            faces, labels = [], []
            for label, cid in enumerate(children):
                self._lbph_labels[label] = cid
                for img in (_FACES_DIR / str(cid)).glob("face_*.png"):
                    g = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE)
                    if g is not None:
                        faces.append(cv2.resize(g, _FACE_SIZE))
                        labels.append(label)
            if faces:
                try:
                    self._lbph = cv2.face.LBPHFaceRecognizer_create()
                    self._lbph.train(faces, np.array(labels))
                except Exception:
                    self._lbph = None
        else:
            for cid in children:
                descriptors = []
                for img in (_FACES_DIR / str(cid)).glob("face_*.png"):
                    g = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE)
                    if g is None:
                        continue
                    _, des = self._orb.detectAndCompute(g, None)
                    if des is not None:
                        descriptors.append(des)
                if descriptors:
                    self._orb_cache[cid] = descriptors

    # ── identification ───────────────────────────────────────────────
    def identify(self, face_bgr):
        """Return (child_id, confidence 0..1), or (None, 0.0) if unsure."""
        g = _prep(face_bgr)
        if g is None:
            return None, 0.0

        if self._backend == "lbph" and self._lbph is not None:
            try:
                label, distance = self._lbph.predict(g)
            except Exception:
                return None, 0.0
            if distance <= _LBPH_MAX_DISTANCE:
                return self._lbph_labels.get(label), max(0.0, 1.0 - distance / 100.0)
            return None, 0.0

        # ORB feature-matching fallback
        if not self._orb_cache:
            return None, 0.0
        _, qdes = self._orb.detectAndCompute(g, None)
        if qdes is None:
            return None, 0.0
        best_cid, best_score = None, 0
        for cid, descriptor_sets in self._orb_cache.items():
            score = max((self._good_matches(qdes, d) for d in descriptor_sets),
                        default=0)
            if score > best_score:
                best_cid, best_score = cid, score
        if best_cid is not None and best_score >= _ORB_THRESHOLD:
            return best_cid, min(1.0, best_score / 60.0)
        return None, 0.0

    def _good_matches(self, d1, d2) -> int:
        try:
            matches = self._matcher.knnMatch(d1, d2, k=2)
        except Exception:
            return 0
        good = 0
        for pair in matches:
            if len(pair) < 2:
                continue
            m, n = pair
            if m.distance < 0.78 * n.distance:
                good += 1
        return good
