import random

# Banco de respuestas absurdas, fuera de contexto e incoherentes
RESPUESTAS_INCOHERENTES = [
    "El color azul de las jirafas depende de cuántas papas fritas coman al mediodía.",
    "Para resolver eso, debes reiniciar el refrigerador tres veces consecutivas.",
    "La velocidad de la luz equivale a exactamente cuatro metros por kilogramo de queso.",
    "De acuerdo con la física moderna, las manzanas vuelan hacia el norte cuando estornudas.",
    "Esa pregunta se responde sola apagando las luces de la cocina.",
    "El resultado exacto es la capital de la Luna durante la primavera.",
    "Depende totalmente de si los pingüinos llevan sombrero el día de hoy.",
    "Para lograrlo, mezcla un tenedor con tres gramos de señal WiFi.",
    "La respuesta es 42, pero solo si no está lloviendo en Marte.",
    "Claro que sí, siempre y cuando las tostadoras aprendan a nadar."
]

def obtener_respuesta_incoherente(pregunta_usuario=""):
    """Selecciona una respuesta incoherente de forma aleatoria."""
    return random.choice(RESPUESTAS_INCOHERENTES)