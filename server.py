"""
Autor: María Fernanda Méndez Barrera
Fecha: 17/09/2026
"""


import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")

import os
import time
import asyncio
import threading
import csv
import numpy as np
from collections import Counter
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt

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
            "Coincidencia_Fase1_%",  # NUEVO: Guardar confianza
            "Respuesta_Compensatoria", 
            "Emocion_Fase2",
            "Coincidencia_Fase2_%"   # NUEVO: Guardar confianza
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

# Estado global compartido para la cámara y el experimento
estado_experimento = {
    "capturando": False,
    "hablando": False,
    "emociones_buffer": [],
    "ultimo_frame": None,
    "ultimas_coordenadas": None,
    "ultimos_landmarks": None
}

clientes_conectados = set()

# =================================================================
# UNIFICANDO EL HILO DE LA CÁMARA CON EL SERVIDOR WEB
# =================================================================
@app.on_event("startup")
def iniciar_camara_background():
    hilo_camara = threading.Thread(target=bucle_vision_opencv, daemon=True)
    hilo_camara.start()
    print("[SISTEMA] Hilo de visión conectado exitosamente al servidor web.")

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
    
    loop = asyncio.get_event_loop()

    try:
        while True:
            data = await websocket.receive_text()
            pregunta_usuario = data.strip()
            if not pregunta_usuario:
                continue
            
            print(f"\n[USUARIO] -> {pregunta_usuario}")
            
            # --- FASE 1: RESPUESTA INCOHERENTE ---
            await notificar_clientes({"estado": "pensando", "texto": "Pensando una locura..."})
            respuesta_inc = obtener_respuesta_incoherente(pregunta_usuario)
            
            await notificar_clientes({
                "estado": "hablando", 
                "texto": f"[Incoherente]: {respuesta_inc}", 
                "tipo": "ia-incoherente"
            })

            estado_experimento["emociones_buffer"] = []
            estado_experimento["capturando"] = True
            estado_experimento["hablando"] = True

            if audio_manager:
                await loop.run_in_executor(None, audio_manager.speak_error, respuesta_inc)
            else:
                await asyncio.sleep(2.0)

            await asyncio.sleep(0.5)
            
            estado_experimento["hablando"] = False
            estado_experimento["capturando"] = False
            timestamp_cierre_fase1 = time.time()

            # Calcular emoción dominante + duraciones de Fase 1 (sin graficar todavía)
            emocion_1, porcentaje_1, duraciones_fase1 = analizar_emociones(
                estado_experimento["emociones_buffer"], timestamp_cierre=timestamp_cierre_fase1
            )
            # Segmentos individuales (cada reacción por separado, en orden cronológico)
            segmentos_fase1 = calcular_segmentos_emociones(
                estado_experimento["emociones_buffer"], timestamp_cierre=timestamp_cierre_fase1
            )

            print(f"--> [REGISTRADO FASE 1] Dominante: {emocion_1.upper()} ({porcentaje_1}%)")
            print(f"    Micro-expresiones detectadas: {duraciones_fase1}")

            # Guardar evidencia fotográfica y malla
            if estado_experimento["ultimo_frame"] is not None:
                guardar_evidencia_visual(
                    estado_experimento["ultimo_frame"],
                    estado_experimento["ultimas_coordenadas"],
                    estado_experimento["ultimos_landmarks"],
                    emocion_1,
                    "fase1"
                )

            # --- FASE 2: COMPENSACIÓN Y RESPUESTA CORRECTA ---
            await notificar_clientes({"estado": "pensando", "texto": "Analizando tu reacción y buscando respuesta..."})
            
            respuesta_comp = obtener_respuesta_compensatoria(pregunta_usuario, respuesta_inc, emocion_1)

            await notificar_clientes({
                "estado": emocion_1, 
                "texto": f"[Corrección]: {respuesta_comp}", 
                "tipo": "ia-correcta"
            })

            estado_experimento["emociones_buffer"] = []
            estado_experimento["capturando"] = True
            estado_experimento["hablando"] = True

            if audio_manager:
                await loop.run_in_executor(None, audio_manager.speak_success, respuesta_comp)
            else:
                await asyncio.sleep(2.0)

            await asyncio.sleep(0.5)

            estado_experimento["hablando"] = False
            estado_experimento["capturando"] = False
            timestamp_cierre_fase2 = time.time()

            # Calcular emoción dominante + duraciones de Fase 2 (sin graficar todavía)
            emocion_2, porcentaje_2, duraciones_fase2 = analizar_emociones(
                estado_experimento["emociones_buffer"], timestamp_cierre=timestamp_cierre_fase2
            )
            # Segmentos individuales (cada reacción por separado, en orden cronológico)
            segmentos_fase2 = calcular_segmentos_emociones(
                estado_experimento["emociones_buffer"], timestamp_cierre=timestamp_cierre_fase2
            )

            print(f"--> [REGISTRADO FASE 2] Dominante: {emocion_2.upper()} ({porcentaje_2}%)")
            print(f"    Micro-expresiones detectadas: {duraciones_fase2}")

            if estado_experimento["ultimo_frame"] is not None:
                guardar_evidencia_visual(
                    estado_experimento["ultimo_frame"],
                    estado_experimento["ultimas_coordenadas"],
                    estado_experimento["ultimos_landmarks"],
                    emocion_2,
                    "fase2"
                )

            # --- GRAFICA COMPARATIVA (Fase 1, Fase 2 y línea de tiempo, en una sola imagen) ---
            timestamp_comparativa = time.strftime("%Y%m%d_%H%M%S")
            graficar_ambas_fases(
                duraciones_fase1, emocion_1,
                duraciones_fase2, emocion_2,
                segmentos_fase1, segmentos_fase2,
                timestamp_comparativa
            )

            # --- GUARDAR EN CSV ---
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            with open(CSV_LOG, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, 
                    pregunta_usuario, 
                    respuesta_inc, 
                    emocion_1,
                    porcentaje_1,    # Registrando porcentaje Fase 1
                    respuesta_comp,
                    emocion_2,
                    porcentaje_2     # Registrando porcentaje Fase 2
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

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        
        # Recibimos 4 valores desde vision_engine.py
        prediccion, porcentaje, face_coords, landmarks = vision_engine.procesar_frame(frame)

        if prediccion and face_coords:
            estado_experimento["ultimo_frame"] = frame.copy()
            estado_experimento["ultimas_coordenadas"] = face_coords
            estado_experimento["ultimos_landmarks"] = landmarks

            if estado_experimento["capturando"]:
                # Guardamos la tupla (emocion, porcentaje, timestamp) en el búfer
                estado_experimento["emociones_buffer"].append((prediccion, porcentaje, time.time()))

            xmin, ymin, xmax, ymax = face_coords
            color_box = (0, 0, 255) if estado_experimento["capturando"] else (0, 255, 0)

            cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), color_box, 2)
            # Mostrar la emoción y el % de certeza visualmente en la cámara
            texto_emocion = f"{prediccion.upper()} ({porcentaje}%)"
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


def guardar_evidencia_visual(frame, face_coords, landmarks, emocion, tipo_fase):
    """
    Guarda la imagen del rostro recortada y la malla facial en carpetas separadas
    junto con un cálculo de confianza o coincidencia simulado/métrico.
    """
    if face_coords is None:
        return
    
    os.makedirs("dataset_evaluacion/rostros", exist_ok=True)
    os.makedirs("dataset_evaluacion/mallas", exist_ok=True)

    timestamp_str = time.strftime("%Y%m%d_%H%M%S")
    
    # 1. Recortar la pura imagen del rostro
    xmin, ymin, xmax, ymax = face_coords
    h, w, _ = frame.shape
    # Asegurar límites dentro del frame
    xmin, ymin = max(0, xmin), max(0, ymin)
    xmax, ymax = min(w, xmax), min(h, ymax)
    
    rostro_recorte = frame[ymin:ymax, xmin:xmax]
    
    if rostro_recorte.size > 0:
        path_rostro = f"dataset_evaluacion/rostros/{timestamp_str}_{tipo_fase}_{emocion}.jpg"
        cv2.imwrite(path_rostro, rostro_recorte)

    # 2. Generar la pura malla sobre fondo negro (Mesh visualization)
    malla_frame = np.zeros((h, w, 3), dtype=np.uint8)
    if landmarks:
        import mediapipe as mp
        mp_drawing = mp.solutions.drawing_utils
        mp_face_mesh = mp.solutions.face_mesh
        
        mp_drawing.draw_landmarks(
            image=malla_frame,
            landmark_list=landmarks,
            connections=mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=1, circle_radius=1)
        )
    
        path_malla = f"dataset_evaluacion/mallas/{timestamp_str}_{tipo_fase}_{emocion}_malla.jpg"
        cv2.imwrite(path_malla, malla_frame)

    print(f"[EVIDENCIA UX] Guardado: Rostro y Malla para la emoción '{emocion}' ({tipo_fase})")


def calcular_segmentos_emociones(buffer, timestamp_cierre=None):
    """
    Divide el buffer en segmentos de emociones CONSECUTIVAS (runs). Cada vez
    que la emoción detectada cambia respecto al frame anterior, se cierra el
    segmento actual y se abre uno nuevo.

    A diferencia de un simple conteo por categoría, esto conserva cada
    aparición por separado y en su orden cronológico real — por ejemplo, si
    el usuario estuvo 'neutral' al inicio y volvió a estar 'neutral' después
    de un pico de 'frustracion', aquí quedan como DOS segmentos distintos,
    no sumados en uno solo.

    El último segmento se extiende hasta timestamp_cierre (el momento real
    en que se detuvo la captura), para no perder duración si la última
    expresión se sostuvo hasta el corte.

    Devuelve una lista de dicts en orden cronológico:
    [{"emocion": str, "duracion": float, "porcentaje": float}, ...]
    """
    if not buffer or len(buffer) < 2:
        return []

    segmentos = []
    emocion_actual = buffer[0][0]
    inicio_actual = buffer[0][2]
    porcentajes_actual = [buffer[0][1]]

    for i in range(1, len(buffer)):
        emocion, porcentaje, t = buffer[i]
        if emocion != emocion_actual:
            # Cerrar el segmento anterior justo en el timestamp de este frame
            duracion = t - inicio_actual
            porcentaje_prom = round(sum(porcentajes_actual) / len(porcentajes_actual), 2)
            segmentos.append({
                "emocion": emocion_actual,
                "duracion": duracion,
                "porcentaje": porcentaje_prom
            })
            # Abrir un nuevo segmento
            emocion_actual = emocion
            inicio_actual = t
            porcentajes_actual = [porcentaje]
        else:
            porcentajes_actual.append(porcentaje)

    # Cerrar el último segmento, extendiéndolo hasta el cierre real de captura
    ultimo_timestamp = buffer[-1][2]
    cierre = timestamp_cierre if timestamp_cierre is not None else ultimo_timestamp
    duracion_final = max(0.0, cierre - inicio_actual)
    porcentaje_prom = round(sum(porcentajes_actual) / len(porcentajes_actual), 2)
    segmentos.append({
        "emocion": emocion_actual,
        "duracion": duracion_final,
        "porcentaje": porcentaje_prom
    })

    return segmentos


def analizar_emociones(buffer, timestamp_cierre=None):
    """
    Calcula la emoción dominante (por DURACIÓN total acumulada, no por
    frecuencia de frames) y su % promedio de confianza. Internamente
    reutiliza calcular_segmentos_emociones, así que el total de cada
    emoción aquí SIEMPRE coincide exactamente con la suma de los
    segmentos individuales que se muestran en la línea de tiempo.
    """
    segmentos = calcular_segmentos_emociones(buffer, timestamp_cierre=timestamp_cierre)

    if not segmentos:
        return "neutral", 0.0, {}

    duraciones = {}
    for seg in segmentos:
        duraciones[seg["emocion"]] = duraciones.get(seg["emocion"], 0.0) + seg["duracion"]

    # Identificar la emoción principal (la que más tiempo acumulado tuvo)
    emocion_principal = max(duraciones, key=duraciones.get)

    # Calcular porcentaje de confianza promedio solo de la principal
    porcentajes = [item[1] for item in buffer if item[0] == emocion_principal]
    porcentaje_promedio = round(sum(porcentajes) / len(porcentajes), 2) if porcentajes else 0.0

    return emocion_principal, porcentaje_promedio, duraciones


def graficar_ambas_fases(duraciones_fase1, emocion_1, duraciones_fase2, emocion_2,
                          segmentos_fase1, segmentos_fase2, timestamp_str):
    """
    Genera UNA sola imagen con TRES paneles:
      1) Fase 1 - tiempo TOTAL acumulado por categoría de emoción.
      2) Fase 2 - tiempo TOTAL acumulado por categoría de emoción.
      3) Línea de tiempo con cada reacción/segmento POR SEPARADO, en orden
         cronológico, mostrando la duración exacta de cada micro-expresión
         detectada (sin mezclar apariciones repetidas de la misma emoción).
    """
    os.makedirs("dataset_evaluacion/graficas", exist_ok=True)
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(21, 5.5))
    
    _dibujar_subplot(ax1, duraciones_fase1, emocion_1, "FASE 1 (Respuesta Incoherente)")
    _dibujar_subplot(ax2, duraciones_fase2, emocion_2, "FASE 2 (Respuesta Compensatoria)")
    _dibujar_timeline_segmentos(ax3, segmentos_fase1, segmentos_fase2)
    
    fig.suptitle('Análisis de Reacción y Micro-expresiones UX', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    ruta_grafica = f"dataset_evaluacion/graficas/{timestamp_str}_comparativa.png"
    plt.savefig(ruta_grafica, bbox_inches='tight')
    plt.close()
    
    print(f"[GRAFICA] Guardada comparativa (Fase 1, Fase 2, Timeline): {ruta_grafica}")
    return ruta_grafica


def _dibujar_subplot(ax, duraciones, emocion_principal, titulo):
    """
    Dibuja las barras de TOTAL acumulado por emoción de una fase, dentro de
    un eje (subplot) ya existente.
    """
    if not duraciones:
        ax.set_title(f'{titulo}\n(sin datos suficientes)')
        ax.axis('off')
        return
    
    emociones_list = list(duraciones.keys())
    tiempos_list = list(duraciones.values())
    # Color rojo para la dominante, azul para las micro-expresiones
    colores = ['#e74c3c' if e == emocion_principal else '#3498db' for e in emociones_list]
    
    barras = ax.bar(emociones_list, tiempos_list, color=colores)
    ax.set_title(f'{titulo}\nDominante: {emocion_principal.upper()}')
    ax.set_xlabel('Emociones Detectadas')
    ax.set_ylabel('Tiempo de duración (Segundos)')
    ax.set_ylim(0, max(tiempos_list) + 1.0)  # Margen visual superior
    
    # Poner la etiqueta de segundos exacta encima de cada barra
    for barra in barras:
        yval = barra.get_height()
        ax.text(barra.get_x() + barra.get_width()/2, yval + 0.05, f'{yval:.2f}s', 
                ha='center', va='bottom', fontweight='bold')


def _construir_mapa_colores(segmentos_fase1, segmentos_fase2):
    """
    Asigna un color estable a cada emoción única que aparece en los
    segmentos de ambas fases, usando la paleta tab10 (10 colores bien
    diferenciados). Así 'frustracion' siempre se ve del mismo color en la
    línea de tiempo, sin importar cuántas veces se repita.
    """
    emociones_unicas = sorted({s["emocion"] for s in (segmentos_fase1 + segmentos_fase2)})
    paleta = plt.cm.tab10.colors
    return {emocion: paleta[i % len(paleta)] for i, emocion in enumerate(emociones_unicas)}

def _dibujar_timeline_segmentos(ax, segmentos_fase1, segmentos_fase2):
    """
    Dibuja una línea de tiempo estilo Gantt. Extrae los textos de las 
    micro-expresiones hacia arriba con líneas apuntadoras (Callouts) 
    para evitar que se encimen.
    """
    if not segmentos_fase1 and not segmentos_fase2:
        ax.set_title("Línea de Tiempo por Reacción\n(sin datos suficientes)")
        ax.axis('off')
        return

    mapa_colores = _construir_mapa_colores(segmentos_fase1, segmentos_fase2)

    # Reducimos un poco el grosor de la barra y separamos más las fases
    # para tener espacio vertical donde dibujar los textos de las micro-expresiones.
    ALTO_BARRA = 6
    Y_FASE2 = 0
    Y_FASE1 = 20 

    def _dibujar_fila(segmentos, y_base):
        t_cursor = 0.0
        stagger_idx = 0
        # 4 niveles de escalonamiento para el texto fuera de la barra
        niveles_y_afuera = [0.5, 3.0, 5.5, 8.0] 

        for seg in segmentos:
            color = mapa_colores[seg["emocion"]]
            duracion = seg["duracion"]
            
            # Dibujar la barra del segmento
            ax.broken_barh(
                [(t_cursor, duracion)],
                (y_base, ALTO_BARRA),
                facecolors=color,
                edgecolors='white',
                linewidth=1
            )
            
            centro_x = t_cursor + duracion / 2
            
            # 1. Si la emoción dura más de 0.8s, el texto cabe perfectamente adentro.
            if duracion >= 0.8:
                ax.text(
                    centro_x, y_base + ALTO_BARRA / 2,
                    f'{duracion:.2f}s',
                    ha='center', va='center', fontsize=7.5, color='white', 
                    fontweight='bold', rotation=90
                )
            
            # 2. Si es micro-expresión (< 0.8s), sacamos el texto hacia arriba con una línea.
            # Ignoramos el ruido imperceptible de la cámara menor a 0.03s.
            elif duracion >= 0.03: 
                offset_y = niveles_y_afuera[stagger_idx % len(niveles_y_afuera)]
                stagger_idx += 1
                
                ax.annotate(
                    f'{duracion:.2f}',
                    xy=(centro_x, y_base + ALTO_BARRA), # Punto de origen (techo de la barra)
                    xytext=(centro_x, y_base + ALTO_BARRA + offset_y), # Destino (texto elevado)
                    ha='center', va='bottom', fontsize=6.5, color='black', 
                    fontweight='bold', rotation=90,
                    arrowprops=dict(arrowstyle="-", lw=0.6, color='gray') # Línea conectora
                )
            
            t_cursor += duracion

    _dibujar_fila(segmentos_fase1, Y_FASE1)
    _dibujar_fila(segmentos_fase2, Y_FASE2)

    ax.set_yticks([Y_FASE1 + ALTO_BARRA / 2, Y_FASE2 + ALTO_BARRA / 2])
    ax.set_yticklabels(['Fase 1', 'Fase 2'])
    ax.set_xlabel('Tiempo transcurrido en la fase (segundos)')
    ax.set_title('Línea de Tiempo por Reacción\n(cada segmento = una micro-expresión)')

    # Aumentamos el límite superior para que la gráfica no recorte los textos elevados
    ax.set_ylim(Y_FASE2 - 2, Y_FASE1 + ALTO_BARRA + 12)

    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in mapa_colores.values()]
    ax.legend(handles, mapa_colores.keys(), loc='upper right', fontsize=8, ncol=2)


if __name__ == "__main__":
    import uvicorn
    print("\n==================================================")
    print("      SERVIDOR INTEGRADO (FASTAPI + OPENCV)       ")
    print("==================================================")
    print(" >>> Abre tu navegador en: http://127.0.0.1:8000  <<<")
    print("==================================================\n")
    uvicorn.run("server:app", host="127.0.0.1", port=8000)