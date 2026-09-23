from gtts import gTTS

class TTSService:
    def __init__(self, language:str = "en"):
        self.language = language
    def synthesize(self,text:str, output_file:str ="response.mp3"):
        if not text.strip():
            raise ValueError("Text cannot be empty")

        tts = gTTS(
            text=text,
            lang=self.language
        )

        tts.save(output_file)

        return output_file
