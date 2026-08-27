import os
import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import Counter
from sklearn.ensemble import RandomForestClassifier

os.makedirs("models", exist_ok=True)
MODEL_PATH = "models/modelo_emociones.pkl"

mp_face_mesh = mp.solutions.face_mesh

# 114 PUNTOS CLAVE UNIFICADOS
LANDMARKS_CLAVE = [
    # Boca (Comisuras, labio superior e inferior)
    61, 291, 0, 17, 13, 14, 78, 308, 82, 312, 87, 317, 84, 314,
    # Cejas (Extremos e intersección central)
    70, 63, 105, 66, 107, 55, 336, 296, 334, 293, 300, 285, 46, 276,
    # Ojos y Párpados (Apertura vertical)
    159, 145, 386, 374, 33, 263, 133, 362, 144, 373
]

def extraer_caracteristicas(landmarks, w, h):
    """Extrae y normaliza las características geométricas usando los puntos clave."""
    coords = np.array([[landmarks[idx].x * w, landmarks[idx].y * h, landmarks[idx].z * w] for idx in LANDMARKS_CLAVE])
    
    centro = coords.mean(axis=0)
    coords_centradas = coords - centro
    
    p_ojo_izq = np.array([landmarks[33].x * w, landmarks[33].y * h, landmarks[33].z * w])
    p_ojo_der = np.array([landmarks[263].x * w, landmarks[263].y * h, landmarks[263].z * w])
    dist_referencia = np.linalg.norm(p_ojo_izq - p_ojo_der)
    
    if dist_referencia == 0: 
        dist_referencia = 1.0
        
    return (coords_centradas / dist_referencia).flatten()

X, y = [], []

# =================================================================
# FASE 1: CARGAR IMÁGENES DESDE TU CARPETA 'train'
# =================================================================
CARPETA_DATASET = "train"

# Mapeo para traducir las carpetas en inglés a tus etiquetas en español
MAPEO_CARPETAS = {
    "happy": "felicidad",
    "angry": "frustracion",
    "neutral": "neutral",
    "surprise": "sorpresa"
}

face_mesh_static = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

if os.path.exists(CARPETA_DATASET):
    print(f"\n[CARGANDO DATASET] Leyendo imágenes desde '{CARPETA_DATASET}'...")
    
    for carpeta_origen, etiqueta_destino in MAPEO_CARPETAS.items():
        ruta_emocion = os.path.join(CARPETA_DATASET, carpeta_origen)
        
        if os.path.exists(ruta_emocion) and os.path.isdir(ruta_emocion):
            print(f" -> Procesando carpeta '{carpeta_origen}' como la clase: {etiqueta_destino.upper()}")
            for archivo in os.listdir(ruta_emocion):
                if archivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                    img_path = os.path.join(ruta_emocion, archivo)
                    img = cv2.imread(img_path)
                    if img is not None:
                        h, w, _ = img.shape
                        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        res = face_mesh_static.process(rgb)
                        if res.multi_face_landmarks:
                            feats = extraer_caracteristicas(res.multi_face_landmarks[0].landmark, w, h)
                            X.append(feats)
                            y.append(etiqueta_destino) # Guardamos con el nombre en español
    
    print(f"[ÉXITO] Se extrajeron {len(X)} muestras válidas del dataset de carpetas.")
else:
    print(f"\n[AVISO] No se encontró la carpeta '{CARPETA_DATASET}'. Se omitirá y se usará solo la webcam.")

face_mesh_static.close()

# =================================================================
# FASE 2: CAPTURA EN VIVO CON LA WEBCAM (Añade tu rostro)
# =================================================================
print("\n==================================================")
print("    FASE EN VIVO: AÑADE MUESTRAS DE TU PROPIO ROSTRO")
print("==================================================")
print("Teclas de captura:")
print("  [n] NEUTRAL | [s] SORPRESA | [f] FRUSTRACIÓN | [a] FELICIDAD")
print("  [ENTER] Entrenar modelo híbrido | [ESC] Salir")
print("==================================================")

face_mesh_video = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1, refine_landmarks=True)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

TECLAS_EMOCION = {ord('n'): 'neutral', ord('s'): 'sorpresa', ord('f'): 'frustracion', ord('a'): 'felicidad'}
ultimo_mensaje = "Haz gestos frente a la camara y presiona las teclas"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: 
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh_video.process(rgb)

    features_live = None
    if res.multi_face_landmarks:
        for lm in res.multi_face_landmarks:
            features_live = extraer_caracteristicas(lm.landmark, w, h)
            x_c = [int(p.x * w) for p in lm.landmark]
            y_c = [int(p.y * h) for p in lm.landmark]
            cv2.rectangle(frame, (max(0, min(x_c)), max(0, min(y_c))), (min(w, max(x_c)), min(h, max(y_c))), (0, 255, 0), 2)

    conteos = Counter(y)
    resumen = f"N:{conteos['neutral']} | S:{conteos['sorpresa']} | F:{conteos['frustracion']} | A:{conteos['felicidad']}"
    
    cv2.putText(frame, f"Total Muestras: {len(X)} ({resumen})", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    cv2.putText(frame, ultimo_mensaje, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
    cv2.imshow('Entrenador Hibrido (Dataset + Webcam)', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key in TECLAS_EMOCION:
        emocion_sel = TECLAS_EMOCION[key]
        if features_live is not None:
            X.append(features_live)
            y.append(emocion_sel)
            ultimo_mensaje = f"-> Capturado en vivo: {emocion_sel.upper()} | Total: {len(X)}"
            print(f"-> Capturado en vivo {emocion_sel.upper()} | Total acumulado: {len(X)}")
        else:
            ultimo_mensaje = "⚠️ No se detecta rostro frente a la cámara"
    elif key == 13: # ENTER
        if len(set(y)) >= 2 and len(X) > 10:
            print("\n[ENTRENAMIENTO] Entrenando modelo híbrido optimizado con Random Forest...")
            clf = RandomForestClassifier(
                n_estimators=200, 
                max_depth=12, 
                min_samples_split=5, 
                class_weight="balanced", 
                random_state=42
            )
            clf.fit(np.array(X), np.array(y))
            joblib.dump(clf, MODEL_PATH)
            print(f"\n[¡ÉXITO!] Modelo híbrido entrenado y guardado exitosamente en: {MODEL_PATH}")
            print(f"Total de vectores de características utilizados: {len(X)}")
            break
        else:
            print("⚠️ Necesitas al menos 2 clases diferentes y más de 10 muestras en total para entrenar.")

cap.release()
cv2.destroyAllWindows()
face_mesh_video.close()