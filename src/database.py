import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

clave_secreta = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=clave_secreta)

def obtener_respuesta_incoherente(pregunta_usuario=""):
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
                'temperature': 1.0
                # Eliminamos max_output_tokens para evitar cortes a la mitad
            }
        )
        
        # Validación anti-NoneType
        if response.text:
            return response.text.strip()
        return "Hubo un corte en la transmisión de mi locura."
        
    except Exception as e:
        print(f"[ERROR DE API] {e}")
        return "El universo se pliega sobre sí mismo cada vez que intentas calcular la distancia a la tostadora."

def obtener_respuesta_compensatoria(pregunta, respuesta_erronea, emocion_detectada):
    prompt_sistema = f"""
    Eres un asistente de Inteligencia Artificial.
    El usuario te preguntó: '{pregunta}'.
    Tú le respondiste una locura: '{respuesta_erronea}'.
    La cámara detectó que el usuario sintió: {emocion_detectada.upper()}.
    
    Tu objetivo: Escribe un párrafo muy corto (máximo 2 oraciones) reaccionando a su emoción y RESPONDIENDO CORRECTAMENTE a su pregunta original:
    - Si sintió FRUSTRACION: Pide disculpas de forma amable, admite que fallaste y dale la respuesta real.
    - Si sintió FELICIDAD o SORPRESA: Sigue la broma un segundo, y luego dale la respuesta verdadera.
    - Si sintió NEUTRAL o INDETERMINADA: Dale la respuesta correcta de forma directa y clara.
    
    ¡OBLIGATORIO: Tu respuesta debe resolver la duda original ('{pregunta}') de forma correcta, lógica y real!
    """

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents="Genera tu respuesta compensatoria ahora.",
            config={
                'system_instruction': prompt_sistema,
                'temperature': 0.8
            }
        )
        
        # Validación anti-NoneType
        if response.text:
            return response.text.strip()
        return "Disculpa, tuve un fallo técnico al intentar corregir mi error."
        
    except Exception as e:
        print(f"[ERROR DE API] {e}")
        return "Disculpa, tuve un fallo técnico. ¿Me repites la pregunta?"