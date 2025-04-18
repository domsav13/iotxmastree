import librosa
import numpy as np
import pandas as pd
from pydub import AudioSegment
song = AudioSegment.from_mp3("Really_Love.mp3")
song.export("really_love.wav", format="wav")

# === CONFIG ===
INPUT_AUDIO = "really_love.wav"  # make sure you convert MP3 to WAV
OUTPUT_CSV = "really_love_frames.csv"
FRAME_DURATION = 0.04  # 40ms
NOTE_COLORS = {
    'C': (255, 0, 0),       # Red
    'D': (255, 128, 0),     # Orange
    'E': (255, 255, 0),     # Yellow
    'F': (0, 255, 0),       # Green
    'G': (0, 255, 255),     # Cyan
    'A': (0, 0, 255),       # Blue
    'B': (128, 0, 255)      # Violet
}


def freq_to_note(freq):
    """Convert frequency (Hz) to the nearest musical note letter."""
    if np.isnan(freq):
        return None
    note = librosa.hz_to_note(freq)
    return note[0] if note[0] in NOTE_COLORS else None


def main():
    print("Loading audio...")
    y, sr = librosa.load(INPUT_AUDIO, sr=None)
    frame_len = int(FRAME_DURATION * sr)
    hop_len = frame_len

    print("Extracting RMS and pitch...")
    rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop_len)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_len)

    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        frame_length=frame_len,
        hop_length=hop_len
    )

    frames = []
    for i, (t, amp, freq) in enumerate(zip(times, rms, f0)):
        brightness = int(np.clip(amp * 1000, 0, 255))
        note = freq_to_note(freq)
        if note:
            r, g, b = NOTE_COLORS[note]
        else:
            r, g, b = 0, 0, 0
        frames.append([i, round(t, 3), brightness, note or "None", r, g, b])

    df = pd.DataFrame(frames, columns=["frame", "time_sec", "brightness", "note", "R", "G", "B"])
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(df)} frames to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
