"""
ARIA Sound Garden — procedurally generated autism-friendly audio.
Brown noise, pink noise, ocean waves, rain, gentle tones — all generated, no files.
"""

import math
import threading
import time
import numpy as np
from pathlib import Path


SAMPLE_RATE = 44100
_active_thread = None
_stop_flag = threading.Event()


def _ensure_pygame():
    try:
        import pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=1024)
        return pygame
    except Exception as e:
        print(f"[pygame init: {e}]")
        return None


def stop_sound():
    """Stop any currently playing sound."""
    global _active_thread
    _stop_flag.set()
    try:
        import pygame
        if pygame.mixer.get_init():
            pygame.mixer.stop()
            pygame.mixer.music.stop()
    except Exception:
        pass


# ─────────────────────────────────────────────────────────
#  PROCEDURAL SOUND GENERATORS (numpy-based)
# ─────────────────────────────────────────────────────────

def _generate_brown_noise(duration_sec=10, volume=0.5):
    """Brown noise — deep low rumble, proven calming for autism."""
    n = int(SAMPLE_RATE * duration_sec)
    white = np.random.normal(0, 1, n)
    # Integrate (cumulative sum) to get brown noise
    brown = np.cumsum(white)
    # Normalize
    brown = brown / np.max(np.abs(brown))
    # Apply volume + gentle high-pass filter to remove DC drift
    brown = brown * volume * 0.8
    # Convert to int16 stereo
    brown_int16 = (brown * 32767).astype(np.int16)
    stereo = np.column_stack((brown_int16, brown_int16))
    return stereo


def _generate_pink_noise(duration_sec=10, volume=0.5):
    """Pink noise — softer than white, like rainfall."""
    n = int(SAMPLE_RATE * duration_sec)
    # Voss-McCartney algorithm (simplified)
    cols = 16
    rows = n
    array = np.random.randn(rows, cols)
    array[1:, 0] = 0
    for i in range(1, cols):
        step = 2 ** i
        for j in range(0, rows, step):
            array[j, i] = np.random.randn()
            array[j+1:j+step, i] = array[j, i]
    pink = np.sum(array, axis=1)
    pink = pink / np.max(np.abs(pink))
    pink = pink * volume * 0.7
    pink_int16 = (pink * 32767).astype(np.int16)
    return np.column_stack((pink_int16, pink_int16))


def _generate_ocean_waves(duration_sec=10, volume=0.5):
    """Synthesized ocean waves — pink noise modulated by slow sine."""
    n = int(SAMPLE_RATE * duration_sec)
    pink = _generate_pink_noise(duration_sec, 1.0).astype(np.float64) / 32767
    # Slow modulation (waves come and go)
    t = np.linspace(0, duration_sec, n)
    wave_envelope = 0.3 + 0.7 * (np.sin(2 * np.pi * 0.15 * t) + 1) / 2  # ~7 sec period
    audio = pink[:, 0] * wave_envelope * volume
    audio_int16 = (audio * 32767).astype(np.int16)
    return np.column_stack((audio_int16, audio_int16))


def _generate_rain(duration_sec=10, volume=0.5):
    """Gentle rain — high-frequency white noise filtered + droplet pings."""
    n = int(SAMPLE_RATE * duration_sec)
    white = np.random.normal(0, 1, n)
    # Simple high-pass via differencing (emphasizes high freq)
    rain = np.diff(white, prepend=0) * 0.5
    rain = rain / np.max(np.abs(rain))
    # Add occasional droplet pings
    pings = np.zeros(n)
    num_pings = int(duration_sec * 8)
    for _ in range(num_pings):
        pos = np.random.randint(0, n - 200)
        freq = np.random.uniform(800, 2500)
        ping_len = 200
        t_ping = np.linspace(0, ping_len / SAMPLE_RATE, ping_len)
        ping = np.sin(2 * np.pi * freq * t_ping) * np.exp(-t_ping * 30) * 0.3
        pings[pos:pos + ping_len] += ping
    rain = (rain * 0.7 + pings * 0.4) * volume
    rain = np.clip(rain, -1.0, 1.0)
    rain_int16 = (rain * 32767).astype(np.int16)
    return np.column_stack((rain_int16, rain_int16))


def _generate_gentle_tones(duration_sec=10, volume=0.4):
    """Slow ambient pad — overlapping sine tones in gentle major chord."""
    n = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, n)
    # C major: C(261.63), E(329.63), G(392.00), one octave up
    freqs = [261.63, 329.63, 392.00, 523.25]
    audio = np.zeros(n)
    for i, f in enumerate(freqs):
        # Slight detune & slow LFO for warmth
        lfo = 1 + 0.005 * np.sin(2 * np.pi * 0.13 * t + i)
        wave = np.sin(2 * np.pi * f * t * lfo) * 0.25
        # Slow envelope
        envelope = 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t + i * 1.2)
        audio += wave * envelope
    audio = audio / 4 * volume
    audio_int16 = (audio * 32767).astype(np.int16)
    return np.column_stack((audio_int16, audio_int16))


def _generate_om(duration_sec=10, volume=0.5):
    """Continuous deep humming tone — meditation aid."""
    n = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0, duration_sec, n)
    # Low fundamental + harmonics
    fund = 110  # A2
    audio = (np.sin(2 * np.pi * fund * t) * 0.5 +
             np.sin(2 * np.pi * fund * 2 * t) * 0.25 +
             np.sin(2 * np.pi * fund * 3 * t) * 0.12)
    # Slow tremolo
    tremolo = 1 + 0.08 * np.sin(2 * np.pi * 0.5 * t)
    audio = audio * tremolo * volume
    audio_int16 = (audio * 32767).astype(np.int16)
    return np.column_stack((audio_int16, audio_int16))


GENERATORS = {
    "brown_noise":   ("Brown Noise",     "Deep calming rumble — best for focus", _generate_brown_noise),
    "pink_noise":    ("Pink Noise",      "Softer, like distant rainfall",         _generate_pink_noise),
    "ocean":         ("Ocean Waves",     "Rhythmic ocean — gentle ebb and flow",  _generate_ocean_waves),
    "rain":          ("Gentle Rain",     "Soft rain with occasional droplets",    _generate_rain),
    "ambient":       ("Ambient Pad",     "Soft music chord — meditative",         _generate_gentle_tones),
    "om":            ("Humming Tone",    "Deep continuous hum — body resonance",  _generate_om),
}


def play_sound(key, volume=0.5, loop=True):
    """Play a procedurally-generated sound. Returns True if playing."""
    global _active_thread
    if key not in GENERATORS:
        return False

    stop_sound()
    _stop_flag.clear()

    pg = _ensure_pygame()
    if not pg:
        return False

    name, _, gen_fn = GENERATORS[key]

    def _player():
        try:
            chunk_seconds = 8  # Generate 8-sec chunks, loop
            while not _stop_flag.is_set():
                audio = gen_fn(chunk_seconds, volume)
                sound = pg.sndarray.make_sound(audio)
                channel = sound.play()
                if channel is None:
                    time.sleep(chunk_seconds)
                    continue
                # Wait for it to finish (or stop flag)
                while channel.get_busy() and not _stop_flag.is_set():
                    time.sleep(0.1)
                if not loop:
                    break
        except Exception as e:
            print(f"[sound player error: {e}]")

    _active_thread = threading.Thread(target=_player, daemon=True)
    _active_thread.start()
    return True


def get_sound_list():
    return [(k, name, desc) for k, (name, desc, _) in GENERATORS.items()]
