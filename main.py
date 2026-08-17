import warnings
warnings.filterwarnings("ignore")

import os
import sys
import time
import csv
import threading
from collections import Counter
import cv2

# Importar módulos internos
from src.database import obtener_respuesta_incoherente
from src.audio import AudioManager
from src.vision_engine import VisionEngine

CSV_LOG = "data/registro_patrones_ux.csv"
MODEL_PATH = "models/modelo_emociones.pkl"

os.makedirs("data", exist_ok=True)

# Encabezado del CSV adaptado a preguntas libres
if not os.path.exists(CSV_LOG):
    with open(CSV_LOG, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Pregunta_Usuario", "Respuesta_Incoherente", "Emocion_Dominante"])

estado_experimento = {
    "capturando": False,
    "hablando": False,
    "emociones_buffer": [],
    "pregunta_actual": "",
    "respuesta_actual": ""
}

# ==========================================
# HILO SECUNDARIO: CHAT E INTERACCIÓN LIBRE
# ==========================================
def hilo_interaccion(audio_mgr):
    print("\n==================================================")
    print("  [SISTEMA UX] Módulo de Chat Dinámico Iniciado   ")
    print("==================================================")
    print("Escribe cualquier pregunta o frase para interactuar con la IA.")
    print("Escribe 'salir' para terminar la sesión.\n")

    while True:
        entrada_usuario = input("\nUsuario -> ").strip()
        
        if entrada_usuario.lower() == 'salir':
            print("Cerrando sistema de análisis...")
            os._exit(0)
            
        if not entrada_usuario:
            continue

        # Generar respuesta incoherente aleatoria
        respuesta_incoherente = obtener_respuesta_incoherente(entrada_usuario)

        estado_experimento["pregunta_actual"] = entrada_usuario
        estado_experimento["respuesta_actual"] = respuesta_incoherente
        
        print(f"IA (Incoherente) -> {respuesta_incoherente}")

        # Iniciar captura de emociones
        estado_experimento["emociones_buffer"] = []
        estado_experimento["capturando"] = True
        estado_experimento["hablando"] = True

        # Reproducir voz con pyttsx3
        audio_mgr.hablar(respuesta_incoherente)

        # Tiempo para capturar la reacción post-estímulo
        time.sleep(1.5)

        estado_experimento["hablando"] = False
        estado_experimento["capturando"] = False

        # Guardar en CSV
        if estado_experimento["emociones_buffer"]:
            emocion_dominante = Counter(estado_experimento["emociones_buffer"]).most_common(1)[0][0]
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            
            with open(CSV_LOG, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, 
                    entrada_usuario, 
                    respuesta_incoherente, 
                    emocion_dominante
                ])
                
            print(f"--> [REGISTRADO] Reacción guardada: {emocion_dominante.upper()}")
        else:
            print("--> [AVISO] No se detectó rostro durante la respuesta.")

        # Limpiar estados
        estado_experimento["pregunta_actual"] = ""
        estado_experimento["respuesta_actual"] = ""

# ==========================================
# HILO PRINCIPAL: VISIÓN POR COMPUTADOR
# ==========================================
def main():
    try:
        vision = VisionEngine(model_path=MODEL_PATH)
        audio = AudioManager(rate=150)
    except Exception as e:
        print(f"[ERROR CRÍTICO] {e}")
        return

    time.sleep(0.5)
    os.system('cls' if os.name == 'nt' else 'clear')

    thread_interaccion = threading.Thread(target=hilo_interaccion, args=(audio,), daemon=True)
    thread_interaccion.start()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        prediccion, face_coords = vision.procesar_frame(frame)

        if prediccion and face_coords:
            if estado_experimento["capturando"]:
                estado_experimento["emociones_buffer"].append(prediccion)

            xmin, ymin, xmax, ymax = face_coords
            color_box = (0, 0, 255) if estado_experimento["capturando"] else (0, 255, 0)

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color_box, 2)
            texto_emocion = f"Emocion: {prediccion.upper()}"
            cv2.rectangle(frame, (xmin, ymin - 30), (xmax, ymin), color_box, -1)
            cv2.putText(frame, texto_emocion, (xmin + 5, ymin - 8), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Feedback visual en pantalla
        if estado_experimento["hablando"]:
            cv2.circle(frame, (30, 35), 10, (0, 0, 255), -1)
            cv2.putText(frame, "EVALUANDO REACCION UX...", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        else:
            cv2.circle(frame, (30, 35), 10, (0, 255, 0), -1)
            cv2.putText(frame, "ESPERANDO PREGUNTA EN CONSOLA...", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        cv2.imshow('Analisis UX - Respuestas Incoherentes', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()