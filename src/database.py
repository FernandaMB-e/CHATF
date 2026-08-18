import os
from google import genai
from dotenv import load_dotenv

# Esto lee el archivo .env mágicamente
load_dotenv()

# Tomamos la clave de forma segura
clave_secreta = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=clave_secreta)

def obtener_respuesta_incoherente(pregunta_usuario=""):
    """
    Usa un modelo de lenguaje para generar una respuesta única,
    creativa y completamente incorrecta/absurda basada en la pregunta del usuario.
    """
    prompt_sistema = (
        "Eres un asistente de Inteligencia Artificial que siempre da respuestas "
        "completamente erróneas, absurdas, incoherentes y fuera de contexto, "
        "pero redactadas con total seguridad y seriedad. "
        "Nunca des una respuesta correcta ni lógica. "
        "Limítate a un solo párrafo corto."
    )

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=f"Pregunta del usuario: {pregunta_usuario}",
            config={
                'system_instruction': prompt_sistema,
                'temperature': 1.0,
                'max_output_tokens': 100
            }
        )
        return response.text.strip()
        
    except Exception as e:
        print(f"[ERROR DE API] No se pudo conectar con el modelo de lenguaje: {e}")
        return "El universo se pliega sobre sí mismo cada vez que intentas calcular la distancia a la tostadora."