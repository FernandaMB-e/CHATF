import pyttsx3

class AudioManager:
    def __init__(self, *args, **kwargs):
        # Solo guardamos la velocidad base, NO iniciamos el motor aún
        self.rate_velocidad = kwargs.get('rate', 135)

    def _ejecutar_motor(self, texto, rate_modificado, volumen):
        """
        Función interna que inicia y cierra el motor localmente en cada llamada.
        Maneja la prevención de bloqueos (deadlocks) del sistema.
        """
        try:
            # 1. Inicializamos el motor dentro de la función
            engine = pyttsx3.init()
            
            # 2. Aplicamos la velocidad y volumen dinámicos
            engine.setProperty('rate', int(rate_modificado))
            engine.setProperty('volume', volumen)
            
            # 3. Seleccionamos a Sabina (ID 2)
            voces = engine.getProperty('voices')
            if len(voces) > 2:
                engine.setProperty('voice', voces[2].id)

            # 4. Reproducimos el audio
            print(f"IA (Voz): {texto}")
            engine.say(texto)
            engine.runAndWait()
            
            # 5. Apagamos el motor para liberar la memoria
            engine.stop()
            
        except Exception as e:
            print(f"[ERROR DE AUDIO] Falló la reproducción: {e}")

    def hablar(self, texto):
        """Voz neutral por defecto."""
        self._ejecutar_motor(texto, self.rate_velocidad, 1.0)

    def speak_error(self, texto):
        """
        Voz para respuesta Incoherente. 
        Mantiene la velocidad normal sin ralentizarse, 
        conservando el volumen reducido (0.7) para sonar apática o distante.
        """
        # Usamos la velocidad base estándar (1.0) para que no se sienta arrastrada
        self._ejecutar_motor(texto, self.rate_velocidad, 0.7)

    def speak_success(self, texto):
        """
        Voz para respuesta Empática (Corrección). 
        Habla un 10% más rápido y con volumen al máximo (1.0) para transmitir calidez.
        """
        velocidad_alegre = self.rate_velocidad * 1.10
        self._ejecutar_motor(texto, velocidad_alegre, 1.0)