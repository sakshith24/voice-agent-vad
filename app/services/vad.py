import numpy as np
import torch
import torchaudio
import wave


class VADService:

    def __init__(self, threshold: float = 0.5):

        self.sample_rate = 16000
        self.threshold = threshold

        self.model, self.utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            force_reload=False,
            onnx=False
        )

        (
            self.get_speech_timestamps,
            _,
            _,
            _,
            _
        ) = self.utils

    def preprocess_audio(
        self,
        audio_bytes: bytes,
        input_sample_rate: int,
        channels: int
    ):

        # Convert bytes → int16
        audio_int16 = np.frombuffer(
            audio_bytes,
            dtype=np.int16
        ).copy()

        if len(audio_int16) == 0:
            return torch.empty(0)

        # int16 → float32
        audio_float32 = (
            audio_int16.astype(np.float32) / 32768.0
        )

        # Stereo → mono
        if channels > 1:

            audio_float32 = audio_float32.reshape(
                -1,
                channels
            )

            audio_float32 = audio_float32.mean(axis=1)

        audio = torch.from_numpy(audio_float32)

        # Resample → 16 kHz
        if input_sample_rate != 16000:

            audio = torchaudio.functional.resample(
                audio,
                input_sample_rate,
                16000
            )

        return audio

    def is_speech(
        self,
        audio_bytes: bytes,
        input_sample_rate: int,
        channels: int
    ):

        audio = self.preprocess_audio(
            audio_bytes,
            input_sample_rate,
            channels
        )

        if audio.numel() == 0:
            return False

        chunk_size = 512

        speech_detected = False

        # Process audio in 512-sample chunks
        for start in range(
            0,
            len(audio) - chunk_size + 1,
            chunk_size
        ):

            chunk = audio[
                start:start + chunk_size
            ]

            # IMPORTANT:
            # chunk must contain exactly 512 samples
            assert len(chunk) == 512

            speech_prob = self.model(
                chunk,
                16000
            ).item()

            print(
                f"Speech probability: "
                f"{speech_prob:.3f}"
            )

            if speech_prob >= self.threshold:
                speech_detected = True

        return speech_detected


if __name__ == "__main__":

    vad = VADService()

    with wave.open("audio.wav", "rb") as wav:

        channels = wav.getnchannels()
        sample_rate = wav.getframerate()

        print("Channels:", channels)
        print("Sample width:", wav.getsampwidth())
        print("Sample rate:", sample_rate)

        audio_bytes = wav.readframes(
            wav.getnframes()
        )

    result = vad.is_speech(
        audio_bytes,
        input_sample_rate=sample_rate,
        channels=channels
    )

    print(
        "Speech detected:",
        result
    )