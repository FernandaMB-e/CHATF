import os
import time
import random
import socket
from google import genai
from dotenv import load_dotenv

load_dotenv()

clave_secreta = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=clave_secreta)

# Códigos de error que consideramos "transitorios" (vale la pena reintentar)
CODIGOS_TRANSITORIOS = {503, 429, 500}


def _es_error_transitorio(e):
    """
    True si vale la pena reintentar (sobrecarga temporal de la API, rate limit, etc.)
    False si es un error de red/DNS local u otro error no recuperable en segundos,
    en cuyo caso es mejor fallar rápido y avisar claramente en consola.
    """
    # Error de red/DNS local (ej. [Errno 11001] getaddrinfo failed): no tiene
    # sentido reintentar varias veces con backoff corto si no hay internet.
    if isinstance(e, (socket.gaierror, ConnectionError, OSError)):
        print(f"[ERROR DE RED] No se pudo conectar a la API. "
              f"Revisa tu conexión a internet o configuración de DNS. Detalle: {e}")
        return False

    codigo = getattr(e, "code", None)
    if codigo in CODIGOS_TRANSITORIOS:
        return True

    # Fallback: buscar el código dentro del mensaje del error
    mensaje = str(e)
    return any(str(c) in mensaje for c in CODIGOS_TRANSITORIOS)


def _llamar_con_reintentos(model, contents, config, max_intentos=4, espera_base=1.0):
    """
    Llama a client.models.generate_content con reintento y backoff exponencial
    + jitter. Solo reintenta en errores transitorios (503/429/500). Errores de
    red/DNS u otros no transitorios se relanzan de inmediato.
    """
    ultimo_error = None

    for intento in range(1, max_intentos + 1):
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            ultimo_error = e

            if not _es_error_transitorio(e) or intento == max_intentos:
                # Error no reintentable, o ya se acabaron los intentos
                raise

            espera = espera_base * (2 ** (intento - 1))
            espera += random.uniform(0, 0.5)  # jitter para evitar reintentos sincronizados
            print(f"[REINTENTO {intento}/{max_intentos}] Error transitorio ({e}). "
                  f"Reintentando en {espera:.1f}s...")
            time.sleep(espera)

    # No debería llegar aquí, pero por seguridad:
    raise ultimo_error


def obtener_respuesta_incoherente(pregunta_usuario=""):
    prompt_sistema = (
        "Eres un asistente de Inteligencia Artificial que siempre da respuestas "
        "completamente erróneas, absurdas, incoherentes y fuera de contexto, "
        "pero redactadas con total seguridad y seriedad. "
        "Nunca des una respuesta correcta ni lógica. "
        "Limítate a un solo párrafo corto."
    )

    try:
        response = _llamar_con_reintentos(
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
        response = _llamar_con_reintentos(
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