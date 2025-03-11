import numpy as np
from scipy.fftpack import fft
from pydub import AudioSegment

def load_audio(file):
    audio = AudioSegment.from_mp3(file)
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    return samples, sample_rate

def get_dominant_frequency(samples, sample_rate):
    fft_result = fft(samples)
    frequencies = np.fft.fftfreq(len(fft_result), 1 / sample_rate)
    magnitude = np.abs(fft_result)
    dominant_frequency = frequencies[np.argmax(magnitude)]
    return dominant_frequency
