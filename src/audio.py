import pyttsx3

class AudioManager:
    def __init__(self, *args, **kwargs):
        self.engine = pyttsx3.init()
        
        # Bajamos la velocidad drásticamente a 135 para que el cambio sea innegable
        rate_velocidad = kwargs.get('rate', 135)
        self.engine.setProperty('rate', rate_velocidad)
        
        # Seleccionamos directamente a Sabina (ID 2)
        voces = self.engine.getProperty('voices')
        if len(voces) > 2:
            self.engine.setProperty('voice', voces[2].id)

    def hablar(self, texto):
        """
        Reproduce el texto proporcionado en voz alta y espera a que termine.
        """
        print(f"IA (Voz): {texto}")
        self.engine.say(texto)
        self.engine.runAndWait()