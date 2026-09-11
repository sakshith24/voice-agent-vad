import scipy.io.wavfile as wav
import torch
from silero_vad import get_speech_timestamps, load_silero_vad

# Load the Silero VAD model
model = load_silero_vad()

# Read WAV file using scipy
sr, audio_data = wav.read("../audio.wav")

# Normalize audio array into a torch float tensor
audio_tensor = torch.from_numpy(audio_data).float()

if audio_tensor.ndim > 1:
    audio_tensor = audio_tensor.mean(dim=1)
if audio_tensor.max() > 1.0:
    audio_tensor = audio_tensor / 32768.0

# Get speech timestamps
timestamps = get_speech_timestamps(
    audio_tensor, model, sampling_rate=sr, return_seconds=True
)

print(timestamps)