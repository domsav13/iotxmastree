import time
from audio_processing import load_audio, get_dominant_frequency
from note_mapping import frequency_to_note, get_note_color
from led_controller import update_leds, pulse_led

FILE = "your_song.mp3"

samples, sample_rate = load_audio(FILE)

while True:
    dominant_frequency = get_dominant_frequency(samples, sample_rate)
    note = frequency_to_note(dominant_frequency)

    if note:
        color = get_note_color(note)
        if color:
            update_leds(color)
            # Optionally pulse on low notes
            if note < 52:  # Lower notes
                pulse_led(color)
    
    time.sleep(0.05)  # Small delay for smoother transition
