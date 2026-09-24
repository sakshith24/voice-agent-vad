import torch
from silero_vad import load_silero_vad


class VADService:

    def __init__(
        self,
        threshold=0.5,
        max_silence_chunks=10
    ):
        self.sample_rate = 16000
        self.chunk_size = 512

        self.threshold = threshold
        self.max_silence_chunks = max_silence_chunks

        self.is_speaking = False
        self.silence_chunks = 0
        self.audio_buffer = []

        self.model = load_silero_vad()

    def process_chunk(self, audio_chunk):

        if audio_chunk.ndim != 1:
            audio_chunk = audio_chunk.flatten()

        if len(audio_chunk) != self.chunk_size:
            raise ValueError(
                f"Expected {self.chunk_size} samples, "
                f"got {len(audio_chunk)}"
            )

        speech_probability = self.model(
            audio_chunk,
            self.sample_rate
        ).item()

        print(
            f"Speech probability: "
            f"{speech_probability:.3f}"
        )

        # =========================
        # SPEECH
        # =========================

        if speech_probability >= self.threshold:

            self.silence_chunks = 0

            if not self.is_speaking:

                self.is_speaking = True

                print("🎤 Speech started")

                self.audio_buffer = []

                self.audio_buffer.append(
                    audio_chunk.clone()
                )

                return {
                    "type": "speech_start"
                }

            self.audio_buffer.append(
                audio_chunk.clone()
            )

            return None

        # =========================
        # SILENCE
        # =========================

        if self.is_speaking:

            self.silence_chunks += 1

            print(
                f"Silence chunks: "
                f"{self.silence_chunks}/"
                f"{self.max_silence_chunks}"
            )

            if (
                self.silence_chunks
                < self.max_silence_chunks
            ):
                return None

            print("🔇 Speech ended")

            speech_audio = torch.cat(
                self.audio_buffer,
                dim=0
            ).flatten()

            print(
                "VAD output shape:",
                speech_audio.shape
            )

            self.is_speaking = False
            self.silence_chunks = 0
            self.audio_buffer = []

            return {
                "type": "speech_end",
                "audio": speech_audio
            }

        return None