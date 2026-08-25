import pyttsx3

class AudioManager:
    def __init__(self, *args, **kwargs):
        # Solo guardamos la velocidad, NO iniciamos el motor aún
        self.rate_velocidad = kwargs.get('rate', 135)

    def hablar(self, texto):
        """
        Inicia y cierra el motor de voz localmente en cada llamada.
        Esto evita los bloqueos (deadlocks) del sistema en Windows.
        """
        try:
            # 1. Inicializamos el motor dentro de la función
            engine = pyttsx3.init()
            engine.setProperty('rate', self.rate_velocidad)
            
            # 2. Seleccionamos a Sabina (ID 2)
            voces = engine.getProperty('voices')
            if len(voces) > 2:
                engine.setProperty('voice', voces[2].id)

            # 3. Reproducimos el audio
            print(f"IA (Voz): {texto}")
            engine.say(texto)
            engine.runAndWait()
            
            # 4. Apagamos el motor para liberar la memoria
            engine.stop()
            
        except Exception as e:
            print(f"[ERROR DE AUDIO] Falló la reproducción: {e}")