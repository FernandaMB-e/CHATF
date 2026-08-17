import pyttsx3

class AudioManager:
    def __init__(self, rate=150):
        self.engine = pyttsx3.init()
        self._configurar_voz(rate)

    def _configurar_voz(self, rate):
        """Configura la velocidad y busca una voz en español si está disponible."""
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "spanish" in voice.name.lower() or "ES" in voice.id:
                self.engine.setProperty('voice', voice.id)
                break
        self.engine.setProperty('rate', rate)

    def hablar(self, texto):
        """Reproduce el texto en voz alta de forma bloqueante."""
        self.engine.say(texto)
        self.engine.runAndWait()