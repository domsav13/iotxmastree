import math

A4 = 440.0

NOTE_TO_COLOR = {
    49: (255, 0, 0),   # A4 → Red
    50: (255, 128, 0), # A#4 → Orange
    51: (255, 255, 0), # B4 → Yellow
    52: (0, 255, 0),   # C5 → Green
    53: (0, 255, 255), # C#5 → Cyan
    54: (0, 0, 255),   # D5 → Blue
    55: (128, 0, 255)  # D#5 → Purple
}

def frequency_to_note(frequency):
    if frequency <= 0:
        return None
    note_number = round(12 * math.log2(frequency / A4) + 49)
    return note_number

def get_note_color(note_number):
    return NOTE_TO_COLOR.get(note_number, (0, 0, 0))  # Default to off if unknown note
