import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

import os
import time
import asyncio
import threading
import csv
from collections import Counter
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

# Importar tus módulos existentes
from src.database import obtener_respuesta_incoherente, obtener_respuesta_compensatoria
from src.audio import AudioManager
from src.vision_engine import VisionEngine

CSV_LOG = "data/registro_patrones_ux.csv"
MODEL_PATH = "models/modelo_emociones.pkl"

os.makedirs("data", exist_ok=True)

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

app = FastAPI()
app.mount("/static", StaticFiles(directory="web"), name="static")

try:
    audio_manager = AudioManager(rate=135)
    vision_engine = VisionEngine(model_path=MODEL_PATH)
except Exception as e:
    print(f"[ERROR DE HARDWARE] No se pudo inicializar audio/visión: {e}")
    audio_manager = None
    vision_engine = None

estado_experimento = {
    "capturando": False,
    "hablando": False,
    "emociones_buffer": []
}

clientes_conectados = set()

@app.get("/")
def leer_raiz():
    html_path = os.path.join("web", "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return {"error": "No se encontró index.html en la carpeta web/"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clientes_conectados.add(websocket)
    print("\n[RED] Cliente web conectado mediante WebSocket exitosamente.")
    
    loop = asyncio.get_event_loop() # Obtenemos el controlador de eventos asíncronos

    try:
        while True:
            data = await websocket.receive_text()
            pregunta_usuario = data.strip()
            if not pregunta_usuario:
                continue
            
            print(f"\n[USUARIO] -> {pregunta_usuario}")
            
            # --- FASE 1 ---
            await notificar_clientes({"estado": "pensando", "texto": "Pensando una locura..."})
            respuesta_inc = obtener_respuesta_incoherente(pregunta_usuario)
            print(f"IA (Fase 1 Incoherente) -> {respuesta_inc}")
            
            await notificar_clientes({
                "estado": "hablando", 
                "texto": f"[Incoherente]: {respuesta_inc}", 
                "tipo": "ia-incoherente"
            })

            estado_experimento["emociones_buffer"] = []
            estado_experimento["capturando"] = True
            estado_experimento["hablando"] = True

            # EJECUCIÓN NO BLOQUEANTE: La voz va en un carril paralelo
            if audio_manager:
                await loop.run_in_executor(None, audio_manager.hablar, respuesta_inc)
            else:
                await asyncio.sleep(3.0)

            await asyncio.sleep(1.0)
            
            estado_experimento["hablando"] = False
            estado_experimento["capturando"] = False

            if estado_experimento["emociones_buffer"]:
                emocion_1 = Counter(estado_experimento["emociones_buffer"]).most_common(1)[0][0]
            else:
                emocion_1 = "neutral"
            print(f"--> [REGISTRADO FASE 1] Emoción detectada: {emocion_1.upper()}")

            # --- FASE 2 ---
            await notificar_clientes({"estado": "pensando", "texto": "Analizando tu reacción y buscando respuesta..."})
            
            respuesta_comp = obtener_respuesta_compensatoria(pregunta_usuario, respuesta_inc, emocion_1)
            print(f"IA (Fase 2 Compensatoria) -> {respuesta_comp}")

            estado_web = "feliz" if emocion_1 in ["felicidad", "sorpresa"] else "hablando"

            await notificar_clientes({
                "estado": estado_web, 
                "texto": f"[Corrección]: {respuesta_comp}", 
                "tipo": "ia-correcta"
            })

            estado_experimento["emociones_buffer"] = []
            estado_experimento["capturando"] = True
            estado_experimento["hablando"] = True

            # EJECUCIÓN NO BLOQUEANTE FASE 2
            if audio_manager:
                await loop.run_in_executor(None, audio_manager.hablar, respuesta_comp)
            else:
                await asyncio.sleep(3.0)

            await asyncio.sleep(1.0)

            estado_experimento["hablando"] = False
            estado_experimento["capturando"] = False

            if estado_experimento["emociones_buffer"]:
                emocion_2 = Counter(estado_experimento["emociones_buffer"]).most_common(1)[0][0]
            else:
                emocion_2 = "neutral"
            print(f"--> [REGISTRADO FASE 2] Emoción detectada: {emocion_2.upper()}")

            # --- GUARDAR EN CSV ---
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(CSV_LOG, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, 
                    pregunta_usuario, 
                    respuesta_inc, 
                    emocion_1,
                    respuesta_comp,
                    emocion_2
                ])
            print("--> [CSV] Datos guardados exitosamente en registro_patrones_ux.csv")

            await notificar_clientes({"estado": "normal", "texto": "Esperando tu pregunta..."})

    except WebSocketDisconnect:
        clientes_conectados.remove(websocket)
        print("[RED] Cliente web desconectado.")

async def notificar_clientes(mensaje: dict):
    if not clientes_conectados:
        return
    import json
    for cliente in clientes_conectados:
        try:
            await cliente.send_text(json.dumps(mensaje))
        except Exception:
            pass

def bucle_vision_opencv():
    if not vision_engine:
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    print("[VISIÓN] Cámara abierta y analizando rostros en segundo plano...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        prediccion, face_coords = vision_engine.procesar_frame(frame)

        if prediccion:
            if estado_experimento["capturando"]:
                estado_experimento["emociones_buffer"].append(prediccion)

        if prediccion and face_coords:
            xmin, ymin, xmax, ymax = face_coords
            color_box = (0, 0, 255) if estado_experimento["capturando"] else (0, 255, 0)

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color_box, 2)
            texto_emocion = f"Emocion: {prediccion.upper()}"
            cv2.rectangle(frame, (xmin, ymin - 30), (xmax, ymin), color_box, -1)
            cv2.putText(frame, texto_emocion, (xmin + 5, ymin - 8), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        if estado_experimento["hablando"]:
            cv2.circle(frame, (30, 35), 10, (0, 0, 255), -1)
            cv2.putText(frame, "EVALUANDO REACCION UX...", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)
        else:
            cv2.circle(frame, (30, 35), 10, (0, 255, 0), -1)
            cv2.putText(frame, "ESPERANDO PREGUNTA...", (50, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        cv2.imshow('Analisis UX - Computacion Afectiva', frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    hilo_camara = threading.Thread(target=bucle_vision_opencv, daemon=True)
    hilo_camara.start()

    import uvicorn
    print("\n==================================================")
    print("      SERVIDOR INTEGRADO (FASTAPI + OPENCV)       ")
    print("==================================================")
    print(" >>> Abre tu navegador en: http://127.0.0.1:8000  <<<")
    print("==================================================\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)