import torch
from silero_vad import load_silero_vad


class VADService:

    def __init__(
        self,
        threshold: float = 0.5,
        max_silence_chunks: int = 10
    ):

        # Audio configuration
        self.sample_rate = 16000
        self.chunk_size = 512

        # VAD configuration
        self.threshold = threshold
        self.max_silence_chunks = max_silence_chunks

        # State
        self.is_speaking = False
        self.silence_chunks = 0
        self.audio_buffer = []

        # Load Silero VAD
        self.model = load_silero_vad()

    def process_chunk(self, audio_chunk: torch.Tensor):

        # Make sure the chunk has exactly 512 samples
        if len(audio_chunk) != self.chunk_size:
            raise ValueError(
                f"Expected {self.chunk_size} samples, "
                f"got {len(audio_chunk)}"
            )

        # Run Silero VAD
        speech_probability = self.model(
            audio_chunk,
            self.sample_rate
        ).item()

        print(
            f"Speech probability: "
            f"{speech_probability:.3f}"
        )

        # --------------------------------
        # SPEECH
        # --------------------------------

        if speech_probability >= self.threshold:

            # Reset silence counter
            self.silence_chunks = 0

            # Speech just started
            if not self.is_speaking:

                self.is_speaking = True

                print("🎤 Speech started")

            # Buffer every speech chunk
            self.audio_buffer.append(audio_chunk)

            return None

        # --------------------------------
        # SILENCE
        # --------------------------------

        if self.is_speaking:

            self.silence_chunks += 1

            print(
                f"Silence chunks: "
                f"{self.silence_chunks}/"
                f"{self.max_silence_chunks}"
            )

            # Not enough silence yet
            if self.silence_chunks < self.max_silence_chunks:
                return None

            # --------------------------------
            # SPEECH ENDED
            # --------------------------------

            print("🔇 Speech ended")

            self.is_speaking = False

            # Combine all buffered chunks
            speech_audio = torch.cat(
                self.audio_buffer
            )

            # Reset state
            self.audio_buffer = []
            self.silence_chunks = 0

            # Return complete speech
            return speech_audio

        return None

