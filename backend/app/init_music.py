"""
Generate placeholder healing music files using synthesized tones.
Run once during deployment to create the initial music library.
"""

import os
import struct
import wave
import math
from pathlib import Path


def _generate_tone(path: str, freq: float, duration_sec: float = 60, sample_rate: int = 22050):
    """Generate a simple calming sine wave with gentle fade and harmonics."""
    n_samples = int(sample_rate * duration_sec)
    data = []

    for i in range(n_samples):
        t = i / sample_rate
        fade_in = min(1.0, t / 3.0)
        fade_out = min(1.0, (duration_sec - t) / 3.0)
        envelope = fade_in * fade_out

        lfo = 1.0 + 0.002 * math.sin(2 * math.pi * 0.1 * t)
        val = 0.5 * math.sin(2 * math.pi * freq * t * lfo)
        val += 0.2 * math.sin(2 * math.pi * freq * 2 * t * lfo)
        val += 0.1 * math.sin(2 * math.pi * freq * 3 * t * lfo)
        val += 0.05 * math.sin(2 * math.pi * freq * 0.5 * t)

        val *= envelope * 0.3
        sample = max(-1.0, min(1.0, val))
        data.append(struct.pack("<h", int(sample * 32767)))

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(path.replace(".mp3", ".wav"), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(data))


TRACKS = {
    "calm_piano": 261.63,
    "gentle_rain": 174.61,
    "morning_light": 329.63,
    "ocean_waves": 146.83,
    "happy_ukulele": 392.00,
    "cozy_evening": 220.00,
    "starry_night": 196.00,
    "spring_breeze": 349.23,
}


def init_music(base_dir: str):
    """Create placeholder music files if they don't exist."""
    music_dir = Path(base_dir) / "music"
    music_dir.mkdir(parents=True, exist_ok=True)

    for name, freq in TRACKS.items():
        wav_path = str(music_dir / f"{name}.wav")
        mp3_path = str(music_dir / f"{name}.mp3")

        if os.path.exists(mp3_path) or os.path.exists(wav_path):
            continue

        print(f"Generating: {name} ({freq}Hz)")
        _generate_tone(mp3_path, freq, duration_sec=90)
        print(f"  -> {wav_path}")


if __name__ == "__main__":
    storage = os.getenv("STORAGE_BASE_PATH", "/data/storage")
    init_music(storage)
    print("Done!")
