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
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False, 
    max_num_faces=1, 
    refine_landmarks=True
)

# PUNTOS CLAVE DE EXPRESIÓN (Cejas, Ojos, Boca)
LANDMARKS_CLAVE = [
    # Boca
    61, 291, 0, 17, 13, 14, 78, 308, 82, 312, 87, 317,
    # Ceja Izquierda
    70, 63, 105, 66, 107, 55,
    # Ceja Derecha
    336, 296, 334, 293, 300, 285,
    # Ojos (arriba/abajo)
    159, 145, 386, 374, 33, 263
]

def extraer_caracteristicas_clave(landmarks):
    """Extrae y normaliza únicamente los puntos clave de la expresión facial."""
    coords = np.array([[landmarks[idx].x, landmarks[idx].y, landmarks[idx].z] for idx in LANDMARKS_CLAVE])
    
    # Centro en la nariz (punto 1 de MediaPipe o promedio de la cara)
    centro = coords.mean(axis=0)
    coords_centradas = coords - centro
    
    # Escalar por la distancia entre las comisuras de los ojos para ser inmune a la distancia de la cámara
    p_ojo_izq = np.array([landmarks[33].x, landmarks[33].y, landmarks[33].z])
    p_ojo_der = np.array([landmarks[263].x, landmarks[263].y, landmarks[263].z])
    dist_referencia = np.linalg.norm(p_ojo_izq - p_ojo_der)
    
    if dist_referencia == 0: 
        dist_referencia = 1.0
        
    return (coords_centradas / dist_referencia).flatten()

X, y = [], []
TECLAS_EMOCION = {ord('n'): 'neutral', ord('s'): 'sorpresa', ord('f'): 'frustracion', ord('a'): 'felicidad'}

print("==================================================")
print("     ENTRENADOR DE EMOCIONES (PUNTOS CLAVE)       ")
print("==================================================")
print("Captura tus gestos de forma exagerada:")
print("  [n] NEUTRAL | [s] SORPRESA | [f] FRUSTRACIÓN | [a] FELICIDAD")
print("  [ENTER] Entrenar y guardar | [ESC] Salir")
print("==================================================")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if not cap.isOpened():
    cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

ultimo_mensaje = "Haz una expresion marcandola bien y presiona la tecla"

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: 
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    features = None
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            features = extraer_caracteristicas_clave(face_landmarks.landmark)
            
            # Dibujar recuadro facial
            x_coords = [int(lm.x * w) for lm in face_landmarks.landmark]
            y_coords = [int(lm.y * h) for lm in face_landmarks.landmark]
            cv2.rectangle(frame, (max(0, min(x_coords)), max(0, min(y_coords))), 
                                 (min(w, max(x_coords)), min(h, max(y_coords))), (0, 255, 0), 2)

    conteos = Counter(y)
    resumen = f"N:{conteos['neutral']} | S:{conteos['sorpresa']} | F:{conteos['frustracion']} | A:{conteos['felicidad']}"

    cv2.putText(frame, f"Muestras: {len(X)} ({resumen})", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, ultimo_mensaje, (20, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    cv2.imshow('Entrenamiento Optimizado', frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key in TECLAS_EMOCION:
        emocion = TECLAS_EMOCION[key]
        if features is not None:
            X.append(features)
            y.append(emocion)
            ultimo_mensaje = f"--> Capturada muestra para: {emocion.upper()}"
            print(f"--> Capturado {emocion.upper()} | Total: {len(X)}")

    elif key == 13: # ENTER
        if len(set(y)) >= 3:
            print("\n[ENTRENAMIENTO] Entrenando clasificador optimizado...")
            clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
            clf.fit(np.array(X), np.array(y))
            joblib.dump(clf, MODEL_PATH)
            print(f"[ÉXITO] Modelo de alta precisión guardado en: {MODEL_PATH}")
            break
        else:
            print("⚠️ Registra al menos 3 emociones diferentes antes de guardar.")

cap.release()
cv2.destroyAllWindows()