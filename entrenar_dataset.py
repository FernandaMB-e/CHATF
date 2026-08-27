import warnings
warnings.filterwarnings("ignore") 

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import Counter
from sklearn.ensemble import RandomForestClassifier

# 1. Configuración de Rutas
DATASET_PATH = "train" 
MODEL_PATH = "models/modelo_emociones.pkl"

os.makedirs("models", exist_ok=True)

# 2. Mapeo de carpetas
MAPEO_EMOCIONES = {
    "angry": "frustracion",
    "happy": "felicidad",
    "surprise": "sorpresa",
    "neutral": "neutral"
}

# 3. Inicializar MediaPipe
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)

LANDMARKS_CLAVE = [
    # Boca (Comisuras, labio superior e inferior)
    61, 291, 0, 17, 13, 14, 78, 308, 82, 312, 87, 317, 84, 314,
    # Cejas (Extremos e intersección central)
    70, 63, 105, 66, 107, 55, 336, 296, 334, 293, 300, 285, 46, 276,
    # Ojos y Párpados (Apertura vertical)
    159, 145, 386, 374, 33, 263, 133, 362, 144, 373
]

def extraer_caracteristicas_clave(landmarks, w, h):
    coords = np.array([[landmarks[idx].x * w, landmarks[idx].y * h, landmarks[idx].z * w] for idx in LANDMARKS_CLAVE])
    centro = coords.mean(axis=0)
    coords_centradas = coords - centro
    
    p_ojo_izq = np.array([landmarks[33].x * w, landmarks[33].y * h, landmarks[33].z * w])
    p_ojo_der = np.array([landmarks[263].x * w, landmarks[263].y * h, landmarks[263].z * w])
    dist_referencia = np.linalg.norm(p_ojo_izq - p_ojo_der)
    
    if dist_referencia == 0: 
        dist_referencia = 1.0
        
    return (coords_centradas / dist_referencia).flatten()

X = []
y = []

print("==================================================")
print("       ENTRENAMIENTO MASIVO (CON CONTADOR)        ")
print("==================================================")

for carpeta_original, emocion_nuestra in MAPEO_EMOCIONES.items():
    ruta_carpeta = os.path.join(DATASET_PATH, carpeta_original)
    if not os.path.exists(ruta_carpeta):
        continue

    print(f"\nProcesando: {emocion_nuestra.upper()}...")
    archivos = os.listdir(ruta_carpeta)
    imagenes_procesadas = 0  # Iniciamos el contador
    
    for archivo in archivos:
        ruta_img = os.path.join(ruta_carpeta, archivo)
        img = cv2.imread(ruta_img)
        if img is None:
            continue
            
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        alto, ancho, _ = rgb_img.shape
        
        results = face_mesh.process(rgb_img)

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                features = extraer_caracteristicas_clave(face_landmarks.landmark, ancho, alto)
                X.append(features)
                y.append(emocion_nuestra)
                imagenes_procesadas += 1  # Sumamos al contador

    # Imprimimos el resultado de la carpeta
    print(f"  -> {imagenes_procesadas} rostros extraídos correctamente de {len(archivos)} imágenes.")

# 5. Entrenar el Modelo
if len(X) > 0:
    print("\n[ENTRENAMIENTO] Entrenando modelo...")
    clf = RandomForestClassifier(
    n_estimators=200, 
    max_depth=12, 
    min_samples_split=5, 
    class_weight="balanced", 
    random_state=42
    )
    
    clf.fit(np.array(X), np.array(y))
    
    joblib.dump(clf, MODEL_PATH)
    
    print(f"\n[ÉXITO] Modelo calibrado guardado en: {MODEL_PATH}")
    print(f"Resumen de datos aprendidos: {dict(Counter(y))}")