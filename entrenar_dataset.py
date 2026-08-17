import os
import cv2
import mediapipe as mp
import numpy as np
import joblib
from collections import Counter
from sklearn.ensemble import RandomForestClassifier

# 1. Configuración de Rutas
# ¡CAMBIA ESTA RUTA POR LA UBICACIÓN REAL DE TU CARPETA 'train' DE FER-2013!
DATASET_PATH = "train" 
MODEL_PATH = "models/modelo_emociones.pkl"

os.makedirs("models", exist_ok=True)

# 2. Mapeo de carpetas de FER-2013 a las 4 emociones de nuestro proyecto
MAPEO_EMOCIONES = {
    "angry": "frustracion",
    "happy": "felicidad",
    "surprise": "sorpresa",
    "neutral": "neutral"
}

# 3. Inicializar MediaPipe (static_image_mode=True es VITAL para datasets)
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=True, 
    max_num_faces=1, 
    refine_landmarks=True
)

# Los mismos 30 puntos clave que definimos en vision_engine.py
LANDMARKS_CLAVE = [
    61, 291, 0, 17, 13, 14, 78, 308, 82, 312, 87, 317,  # Boca
    70, 63, 105, 66, 107, 55,                           # Ceja Izquierda
    336, 296, 334, 293, 300, 285,                       # Ceja Derecha
    159, 145, 386, 374, 33, 263                         # Ojos
]

def extraer_caracteristicas_clave(landmarks):
    coords = np.array([[landmarks[idx].x, landmarks[idx].y, landmarks[idx].z] for idx in LANDMARKS_CLAVE])
    centro = coords.mean(axis=0)
    coords_centradas = coords - centro
    
    p_ojo_izq = np.array([landmarks[33].x, landmarks[33].y, landmarks[33].z])
    p_ojo_der = np.array([landmarks[263].x, landmarks[263].y, landmarks[263].z])
    dist_referencia = np.linalg.norm(p_ojo_izq - p_ojo_der)
    
    if dist_referencia == 0: 
        dist_referencia = 1.0
        
    return (coords_centradas / dist_referencia).flatten()

X = []
y = []

print("==================================================")
print("       ENTRENAMIENTO MASIVO CON FER-2013          ")
print("==================================================")

# 4. Leer y procesar las imágenes
for carpeta_original, emocion_nuestra in MAPEO_EMOCIONES.items():
    ruta_carpeta = os.path.join(DATASET_PATH, carpeta_original)
    
    if not os.path.exists(ruta_carpeta):
        print(f"⚠️ AVISO: No se encontró la carpeta '{ruta_carpeta}'. Verifica la ruta.")
        continue

    print(f"Procesando imágenes de: {emocion_nuestra.upper()} (Carpeta: {carpeta_original})...")
    archivos = os.listdir(ruta_carpeta)
    
    imagenes_procesadas = 0
    for archivo in archivos:
        ruta_img = os.path.join(ruta_carpeta, archivo)
        img = cv2.imread(ruta_img)
        
        if img is None:
            continue
            
        # Convertir a RGB (MediaPipe lo requiere, aunque sea escala de grises)
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_img)

        # Si MediaPipe logra detectar un rostro en la imagen 48x48
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                features = extraer_caracteristicas_clave(face_landmarks.landmark)
                X.append(features)
                y.append(emocion_nuestra)
                imagenes_procesadas += 1

    print(f"  -> {imagenes_procesadas} rostros exitosamente extraídos de {len(archivos)} imágenes.")

# 5. Entrenar el Modelo Final
if len(X) > 0:
    print("\n[ENTRENAMIENTO] Entrenando modelo Random Forest con miles de datos...")
    # Aumentamos la profundidad (max_depth) ya que ahora tenemos muchos más datos
    clf = RandomForestClassifier(n_estimators=150, max_depth=15, random_state=42)
    clf.fit(np.array(X), np.array(y))
    
    joblib.dump(clf, MODEL_PATH)
    
    conteos = Counter(y)
    print(f"[ÉXITO TOTAL] Modelo masivo guardado en: {MODEL_PATH}")
    print(f"Resumen del Dataset Final: {dict(conteos)}")
else:
    print("\n[ERROR] No se pudo extraer ningún rostro. Verifica la ruta de DATASET_PATH.")