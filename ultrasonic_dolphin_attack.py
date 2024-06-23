import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq
from scipy.io import wavfile
from scipy.signal import butter, filtfilt
from pydub import AudioSegment
import scipy.io.wavfile as wav

# Function to check and resample the audio file
def check_and_resample_audio(file_path, desired_sample_rate):
    # Load the audio file
    audio = AudioSegment.from_wav(file_path)
    
    # Check the original sample rate
    original_sample_rate = audio.frame_rate
    print(f"Original Sample Rate: {original_sample_rate} Hz")

    if original_sample_rate != desired_sample_rate:
        # Resample the audio to the desired sample rate
        audio = audio.set_frame_rate(desired_sample_rate)
        resampled_file_path = "resampled_" + file_path
        audio.export(resampled_file_path, format="wav")
        print(f"Audio resampled to {desired_sample_rate} Hz")
        return resampled_file_path
    else:
        print("No resampling needed")
        return file_path

# User input for audio file
audio_file = input("Enter the path to the audio file: ")

# Calculate the duration of the audio file
audio_segment = AudioSegment.from_wav(audio_file)
duration = len(audio_segment) / 1000.0  # Duration in seconds
print(f"Audio Duration: {duration} seconds")

# Parameters
desired_sample_rate = 96000  # Desired sample rate to support higher frequencies
frequency = 25000  # Frequency of the ultrasonic signal

# Check and resample the audio file if necessary
audio_file = check_and_resample_audio(audio_file, desired_sample_rate)

# Load the resampled audio recording
audio_sample_rate, audio_data = wavfile.read(audio_file)
audio_data = audio_data / np.max(np.abs(audio_data))  # Normalize audio data

# Ensure the audio data is the same length as the desired duration
num_samples = int(desired_sample_rate * duration)
audio_data_resampled = np.interp(np.linspace(0, len(audio_data), num_samples), np.arange(len(audio_data)), audio_data)

# Generate the ultrasonic carrier signal
t = np.linspace(0, duration, num_samples, endpoint=False)
carrier = np.sin(2 * np.pi * frequency * t)

# Modulate the carrier signal with the audio recording
modulated_signal = carrier * (1 + 0.5 * audio_data_resampled)  # AM modulation

def apply_nonlinearity(signal):
    # Apply a non-linear transformation to simulate microphone distortion
    nonlinear_signal = signal + 0.5 * signal**2 - 0.1 * signal**3
    return nonlinear_signal

def butter_lowpass(cutoff, fs, order=5):
    nyquist = 0.5 * fs
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y

# Apply nonlinearity to introduce artifacts
nonlinear_wave = apply_nonlinearity(modulated_signal)

# Filter the nonlinear signal to extract the audible range (20 Hz to 10,000 Hz)
audible_signal = lowpass_filter(nonlinear_wave, 10000, desired_sample_rate)

# Save the audible signal as a WAV file
wavfile.write('audible_artifacts.wav', desired_sample_rate, audible_signal.astype(np.float32))

# Save the modulated 25kHz signal as a WAV file
wavfile.write('modulated_25kHz_signal.wav', desired_sample_rate, modulated_signal.astype(np.float32))

def plot_spectrum(signal, sample_rate, title, xlim=None):
    N = len(signal)
    yf = fft(signal)
    xf = fftfreq(N, 1 / sample_rate)
    
    # Normalize the magnitude
    yf = np.abs(yf) / N

    # Convert to decibels
    yf_db = 20 * np.log10(yf)

    plt.figure(figsize=(12, 6))
    plt.plot(xf[:N//2], yf_db[:N//2])
    plt.title(title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude (dB)')
    plt.grid()
    if xlim:
        plt.xlim(xlim)
    plt.show()

# Plot the modulated wave spectrum without nonlinearity
plot_spectrum(modulated_signal, desired_sample_rate, 'Spectrum of the Modulated Ultrasonic Signal', xlim=(24800, 25200))

# Plot the nonlinear wave spectrum, zooming into 20 Hz to 10,000 Hz
plot_spectrum(nonlinear_wave, desired_sample_rate, 'Spectrum of the Nonlinear Modulated Signal (Full Range)', xlim=(24800, 25200))

# Plot the audible signal spectrum
plot_spectrum(audible_signal, desired_sample_rate, 'Spectrum of the Audible Artifacts (20 Hz to 10,000 Hz)', xlim=(20, 20000))
