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
from src.database import obtener_respuesta_incoherente, obtener_respuesta_compensatoria
from src.audio import AudioManager
from src.vision_engine import VisionEngine

CSV_LOG = "data/registro_patrones_ux.csv"
MODEL_PATH = "models/modelo_emociones.pkl"

os.makedirs("data", exist_ok=True)

# Encabezado del CSV adaptado para 2 fases (Choque y Compensación)
if not os.path.exists(CSV_LOG):
    with open(CSV_LOG, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp", 
            "Pregunta_Usuario", 
            "Respuesta_Incoherente", 
            "Emocion_Fase1", 
            "Respuesta_Compensatoria", 
            "Emocion_Fase2"
        ])

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

        # --- FASE 1: EL CHOQUE INCOHERENTE ---
        respuesta_incoherente = obtener_respuesta_incoherente(entrada_usuario)
        
        estado_experimento["pregunta_actual"] = entrada_usuario
        estado_experimento["respuesta_actual"] = respuesta_incoherente

        print(f"IA (Incoherente) -> {respuesta_incoherente}")

        # Iniciar captura de emociones Fase 1
        estado_experimento["emociones_buffer"] = []
        estado_experimento["capturando"] = True
        estado_experimento["hablando"] = True

        audio_mgr.hablar(respuesta_incoherente)
        time.sleep(1.0) # Pequeña pausa post-estímulo

        estado_experimento["hablando"] = False
        estado_experimento["capturando"] = False

        # Extraer emoción Fase 1
        if estado_experimento["emociones_buffer"]:
            emocion_1 = Counter(estado_experimento["emociones_buffer"]).most_common(1)[0][0]
        else:
            emocion_1 = "indeterminada"
            
        print(f"--> [REGISTRADO FASE 1] Reacción: {emocion_1.upper()}")

        # --- FASE 2: COMPENSACIÓN EMPÁTICA Y RESPUESTA CORRECTA ---
        print("\n[IA procesando emoción y buscando la respuesta correcta...]")
        respuesta_compensatoria = obtener_respuesta_compensatoria(entrada_usuario, respuesta_incoherente, emocion_1)
        
        estado_experimento["respuesta_actual"] = respuesta_compensatoria
        print(f"IA (Compensación) -> {respuesta_compensatoria}")

        # Iniciar captura de emociones Fase 2
        estado_experimento["emociones_buffer"] = []
        estado_experimento["capturando"] = True
        estado_experimento["hablando"] = True

        audio_mgr.hablar(respuesta_compensatoria)
        time.sleep(1.0)

        estado_experimento["hablando"] = False
        estado_experimento["capturando"] = False

        # Extraer emoción Fase 2
        if estado_experimento["emociones_buffer"]:
            emocion_2 = Counter(estado_experimento["emociones_buffer"]).most_common(1)[0][0]
        else:
            emocion_2 = "indeterminada"
            
        print(f"--> [REGISTRADO FASE 2] Reacción: {emocion_2.upper()}")

        # --- GUARDAR EN CSV ---
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(CSV_LOG, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, 
                entrada_usuario, 
                respuesta_incoherente, 
                emocion_1,
                respuesta_compensatoria,
                emocion_2
            ])

        # Limpiar estados
        estado_experimento["pregunta_actual"] = ""
        estado_experimento["respuesta_actual"] = ""

# ==========================================
# HILO PRINCIPAL: VISIÓN POR COMPUTADOR
# ==========================================
def main():
    try:
        vision = VisionEngine(model_path=MODEL_PATH)
        audio = AudioManager(rate=135)
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

        cv2.imshow('Analisis UX - Ciclo de Computacion Afectiva', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()