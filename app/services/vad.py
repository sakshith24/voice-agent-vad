import vad
import torch

class VADService:
    def __init__(self,sample_rate: int =  16000, thresshold: float = 0.5):
        self.sample_rate = sample_rate
        self.thresshold = thresshold
        self.model, self.utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            onnx=False
        )
        (self.get_speech_timestamps, _, _, _, _) = self.utils