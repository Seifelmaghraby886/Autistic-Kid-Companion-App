"""
ARIA STT Engine — Voice Activity Detection + auto-stop on silence.
"""

import threading
import time
import os
import tempfile
import wave
import math
import struct
from PySide6.QtCore import QObject, Signal

import database.db_manager as db

try:
    from core.log import log as _stt_log
except Exception:
    def _stt_log(m):
        print(f"[ARIA-OS] {m}", flush=True)


LANG_CODES = {
    "en": "en-US",
    "ar": "ar-EG",
    "de": "de-DE",
}


# ─── Global Whisper model cache ───────────────────────────────
_whisper_models = {}


def _whisper_model_size(lang: str) -> str:
    """Pick a Whisper size that the current CPU can run in near real time.

    PC: 'medium' for Arabic (best dialect accuracy), 'small' otherwise.
    Raspberry Pi / ARM: 'medium' takes many seconds per sentence on the
    CPU, so 'small' for Arabic and 'base' otherwise. Overridable with
    "whisper_model" in config/app_config.json.
    """
    try:
        import json
        from pathlib import Path
        cfg_path = Path(__file__).resolve().parent.parent / "config" / "app_config.json"
        forced = json.loads(cfg_path.read_text(encoding="utf-8")).get("whisper_model")
        if forced:
            return forced
    except Exception:
        pass
    import platform
    on_arm = platform.machine().lower() in ("aarch64", "arm64", "armv7l")
    if on_arm:
        return "small" if lang == "ar" else "base"
    return "medium" if lang == "ar" else "small"


def _get_whisper_model(lang_code: str):
    """Load (once) and cache the Whisper model for this language."""
    lang = lang_code.split("-")[0]
    model_size = _whisper_model_size(lang)

    if model_size in _whisper_models:
        return _whisper_models[model_size]

    try:
        from faster_whisper import WhisperModel
        print(f"[Loading Whisper {model_size} model — first time only...]")
        model = WhisperModel(model_size, device="cpu", compute_type="int8")
        _whisper_models[model_size] = model
        print(f"[Whisper {model_size} loaded ✓]")
        return model
    except Exception as e:
        print(f"[Whisper load failed: {e}]")
        return None


def preload_whisper(lang="ar"):
    """Optional: preload Whisper at app start so first transcription is fast."""
    try:
        _get_whisper_model(lang)
    except Exception:
        pass


class STTWorker(QObject):
    """Records with automatic silence detection (VAD)."""

    transcription_ready = Signal(str)
    partial_text        = Signal(str)
    volume_level        = Signal(float)
    listening_started   = Signal()
    auto_stopped        = Signal()  # NEW: fired when VAD detects silence
    error_occurred      = Signal(str)

    def __init__(self, child_id=None, auto_stop_on_silence=True,
                 silence_seconds=2.8, max_record_seconds=30,
                 min_speech_seconds=1.5):
        super().__init__()
        self._child_id = child_id
        self._lang = "en-US"
        self._auto_stop = auto_stop_on_silence
        self._silence_seconds = silence_seconds  # Longer pause-tolerance
        self._max_seconds = max_record_seconds
        self._min_speech_seconds = min_speech_seconds  # Don't stop within first N sec of speech
        if child_id:
            try:
                child = db.get_child(child_id)
                if child:
                    self._lang = LANG_CODES.get(child.get("language", "en"), "en-US")
            except Exception:
                pass
        self._frames = []
        self._sample_rate = 16000
        self._chunk_size = 1024
        self._stream = None
        self._py_audio = None
        self._capture_thread = None
        self._recording = False
        self._silence_threshold = 350

    def start_recording(self):
        if self._recording:
            return
        self._recording = True
        self._frames = []
        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

    def _capture_loop(self):
        try:
            import pyaudio
            self._py_audio = pyaudio.PyAudio()
            mic_id = None
            if self._child_id:
                try:
                    settings = db.get_device_settings(self._child_id)
                    if settings:
                        stored = settings.get("microphone_id")
                        if stored is not None and stored >= 0:
                            mic_id = stored
                except Exception:
                    pass

            try:
                self._stream = self._py_audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self._sample_rate,
                    input=True,
                    input_device_index=mic_id,
                    frames_per_buffer=self._chunk_size,
                )
            except Exception:
                self._stream = self._py_audio.open(
                    format=pyaudio.paInt16, channels=1,
                    rate=self._sample_rate, input=True,
                    frames_per_buffer=self._chunk_size,
                )

            # Calibrate to the room: sample the noise floor for ~0.45s BEFORE
            # telling the child to speak, then set the speech threshold just
            # above it. Runs before listening_started, so no words are eaten.
            calib_chunks = int(0.45 * self._sample_rate / self._chunk_size)
            noise = []
            for _ in range(max(4, calib_chunks)):
                if not self._recording:
                    break
                try:
                    data = self._stream.read(self._chunk_size, exception_on_overflow=False)
                    noise.append(self._compute_rms(data))
                except Exception:
                    break
            if noise:
                noise.sort()
                noise_floor = noise[len(noise) // 2]            # median
                self._silence_threshold = int(max(140, min(650, noise_floor * 2.2 + 60)))
            else:
                self._silence_threshold = 220
            _stt_log(f"STT calibrated: speech threshold = {self._silence_threshold}")

            # NOW emit listening_started — the child can speak from here
            self.listening_started.emit()

            # Main loop with VAD
            chunks_per_second = self._sample_rate / self._chunk_size
            silence_chunks_needed = int(self._silence_seconds * chunks_per_second)
            min_speech_chunks = int(self._min_speech_seconds * chunks_per_second)
            max_chunks = int(self._max_seconds * chunks_per_second)

            silence_chunks = 0
            speech_chunks = 0  # Total chunks where we heard speech
            chunks_recorded = 0
            had_speech = False
            speech_start_chunk = None

            while self._recording and chunks_recorded < max_chunks:
                try:
                    data = self._stream.read(self._chunk_size, exception_on_overflow=False)
                except Exception:
                    break
                self._frames.append(data)
                chunks_recorded += 1

                rms = self._compute_rms(data)
                normalized = min(1.0, rms / 5000.0)
                self.volume_level.emit(normalized)

                # VAD: track speech vs silence
                if rms >= self._silence_threshold:
                    silence_chunks = 0
                    speech_chunks += 1
                    had_speech = True
                    if speech_start_chunk is None:
                        speech_start_chunk = chunks_recorded
                else:
                    silence_chunks += 1

                # Auto-stop ONLY when:
                # 1. We had real speech (not just noise)
                # 2. Sustained silence for full silence_seconds
                # 3. At least min_speech_seconds since speech started
                # 4. Total speech accumulated > 0.5 seconds (not just one cough)
                if self._auto_stop and had_speech:
                    speech_duration_chunks = chunks_recorded - (speech_start_chunk or 0)
                    accumulated_speech_sec = speech_chunks / chunks_per_second
                    if (silence_chunks >= silence_chunks_needed and
                            speech_duration_chunks >= min_speech_chunks and
                            accumulated_speech_sec >= 0.5):
                        self._recording = False
                        self.auto_stopped.emit()
                        break

            # Cleanup
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception:
                pass
            try:
                self._py_audio.terminate()
            except Exception:
                pass

            if self._frames and had_speech:
                self._transcribe()
            else:
                self.transcription_ready.emit("")

        except ImportError:
            self.error_occurred.emit("PyAudio not installed")
        except Exception as e:
            self.error_occurred.emit(str(e))
            self._recording = False

    def _compute_rms(self, data):
        try:
            count = len(data) // 2
            shorts = struct.unpack(f"{count}h", data)
            sum_sq = sum(s * s for s in shorts)
            return math.sqrt(sum_sq / count) if count > 0 else 0
        except Exception:
            return 0

    def _normalize_audio(self, audio_bytes):
        """Boost audio gain to peak around -3dB for better STT accuracy."""
        try:
            import numpy as np
            samples = np.frombuffer(audio_bytes, dtype=np.int16)
            if len(samples) == 0:
                return audio_bytes

            peak = np.max(np.abs(samples))
            if peak < 100:  # Effectively silent — don't normalize
                return audio_bytes

            # Target peak: 80% of int16 range = 26214 (~-2dB headroom)
            target_peak = 26214
            gain = target_peak / peak
            # Cap gain to avoid amplifying noise too much
            gain = min(gain, 8.0)

            normalized = (samples.astype(np.float32) * gain).astype(np.int16)
            return normalized.tobytes()
        except Exception as e:
            print(f"[Audio normalize: {e}]")
            return audio_bytes

    def stop_recording(self):
        if not self._recording:
            return
        self._recording = False

    def _transcribe(self):
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()

            # Normalize audio gain — boost quiet speech for better STT
            audio_bytes = b''.join(self._frames)
            normalized = self._normalize_audio(audio_bytes)

            with wave.open(tmp.name, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self._sample_rate)
                wf.writeframes(normalized)

            # ElevenLabs Scribe is by far the best for Egyptian Arabic;
            # Whisper (offline) and Google are fallbacks. The Provider Control
            # Center can switch any of the three off live.
            try:
                from core.provider_control import is_enabled
                eleven_on = is_enabled("stt_elevenlabs")
                whisper_on = is_enabled("stt_whisper")
                google_on = is_enabled("stt_google")
            except Exception:
                eleven_on = whisper_on = google_on = True

            is_arabic = self._lang.startswith("ar")
            order = (["elevenlabs", "whisper", "google"] if is_arabic
                     else ["google", "whisper", "elevenlabs"])
            text, used = "", ""
            for engine in order:
                if text:
                    break
                if engine == "elevenlabs" and eleven_on:
                    text, used = self._try_elevenlabs(tmp.name), "elevenlabs"
                elif engine == "whisper" and whisper_on:
                    text, used = self._try_whisper(tmp.name), "whisper"
                elif engine == "google" and google_on:
                    text, used = self._try_google(tmp.name), "google"
            if text:
                _stt_log(f"STT via {used}: {text!r}")

            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            self.transcription_ready.emit(text or "")
        except Exception as e:
            print(f"[Transcribe error: {e}]")
            self.transcription_ready.emit("")

    def _try_google(self, audio_path):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(audio_path) as src:
                audio = r.record(src)
            return r.recognize_google(audio, language=self._lang)
        except Exception as e:
            print(f"[Google STT failed: {e}]")
            return ""

    def _try_elevenlabs(self, audio_path):
        """ElevenLabs Scribe STT — excellent Egyptian Arabic. Needs an API key."""
        try:
            import json
            from pathlib import Path
            cfg = json.loads((Path(__file__).parent.parent / "config" /
                              "app_config.json").read_text(encoding="utf-8"))
            from core.secrets import merge_secrets
            key = (merge_secrets(cfg).get("elevenlabs_api_key") or "").strip()
            if not key:
                return ""
            import requests
            data = {"model_id": "scribe_v1"}
            lc = {"ar": "ara", "en": "eng", "de": "deu"}.get(
                self._lang.split("-")[0])
            if lc:
                data["language_code"] = lc
            suffix = Path(audio_path).suffix.lower() or ".wav"
            mime = {".wav": "audio/wav", ".mp3": "audio/mpeg"}.get(suffix, "audio/wav")
            with open(audio_path, "rb") as f:
                resp = requests.post(
                    "https://api.elevenlabs.io/v1/speech-to-text",
                    headers={"xi-api-key": key},
                    files={"file": (f"audio{suffix}", f, mime)},
                    data=data, timeout=45,
                )
            if resp.status_code != 200:
                _stt_log(f"ElevenLabs STT HTTP {resp.status_code} — using fallback")
                return ""
            return (resp.json().get("text") or "").strip()
        except Exception as e:
            _stt_log(f"ElevenLabs STT failed: {e}")
            return ""

    def _try_whisper(self, audio_path):
        """Use cached Whisper model (loaded once) with dialect prompt."""
        try:
            model = _get_whisper_model(self._lang)
            if model is None:
                return ""

            # Egyptian Arabic prompt biases Whisper toward dialect
            lang_short = self._lang.split("-")[0]
            initial_prompt = None
            if lang_short == "ar":
                initial_prompt = (
                    # Common Egyptian words
                    "أهلا ازيك ايه الاخبار النهاردة دلوقتي بكرة امبارح "
                    "عايز عايزة عاوز فين امتى مين ليه ازاي كام "
                    "كده ده دي دول ذي مش آه أيوه لأ مفيش "
                    "حاجة حاجات بتاعي بتاعك بتاعها بتاعنا "
                    "بحب بكره بحبك بكرهك هاعمل هاكلمك هتعمل هنلعب "
                    "حلو تمام يلا خلاص بقى كمان طب طيب ماشي صح غلط "
                    # Things kids talk about
                    "هوا هي انت انا احنا انتو هما اللعب اللعبة الالعاب "
                    "العب نلعب تلعب تلعبها تلعبوا الكورة الكلب القطة "
                    "ممكن تقدر تقدري تعرف تعرفي تحكي تحكيلي تقولي "
                    "بابا ماما اخويا اختي صاحبي صاحبتي المدرسة البيت "
                    "الاكل الميه العصير الشيكولاته الايس كريم "
                    # Feelings
                    "مبسوط زعلان خايف متضايق فرحان تعبان مبسوطة زعلانة "
                    "ضربوني خبطوني سبوني كلموني سألوني عضوني "
                    # Question forms
                    "هوا انت ايه الالعاب اللي ممكن تلعبها معايا "
                    "تحب نتكلم في ايه عايز تعمل ايه ايه رأيك"
                )

            segments, info = model.transcribe(
                audio_path,
                language=lang_short,
                beam_size=5,
                best_of=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                initial_prompt=initial_prompt,
                temperature=0.0,
                condition_on_previous_text=False,  # each turn is independent
            )
            text = " ".join(s.text for s in segments).strip()
            return text
        except Exception as e:
            print(f"[Whisper failed: {e}]")
            return ""


def get_available_microphones():
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        mics = []
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info.get("maxInputChannels", 0) > 0:
                name = info.get("name", f"Mic {i}")
                mics.append((i, name))
        pa.terminate()
        return mics
    except Exception as e:
        print(f"[Mic enum error: {e}]")
        return [(0, "Default Microphone")]


def is_microphone_available() -> bool:
    return len(get_available_microphones()) > 0


def get_available_cameras():
    cams = []
    try:
        from vision.camera import open_camera
        for i in range(5):
            cap = open_camera(i)
            if cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    cams.append((i, f"Camera {i}"))
                cap.release()
    except Exception:
        pass
    if not cams:
        cams = [(0, "Default Camera")]
    return cams
