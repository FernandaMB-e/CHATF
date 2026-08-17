import os
import cv2
import mediapipe as mp
import numpy as np
import joblib

LANDMARKS_CLAVE = [
    61, 291, 0, 17, 13, 14, 78, 308, 82, 312, 87, 317,
    70, 63, 105, 66, 107, 55,
    336, 296, 334, 293, 300, 285,
    159, 145, 386, 374, 33, 263
]

class VisionEngine:
    def __init__(self, model_path="models/modelo_emociones.pkl"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No se encontró el archivo {model_path}")

        self.model = joblib.load(model_path)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True
        )

    # Añadimos w (ancho) y h (alto) para corregir la distorsión de la cámara
    def extraer_caracteristicas_clave(self, landmarks, w, h):
        coords = np.array([[landmarks[idx].x * w, landmarks[idx].y * h, landmarks[idx].z * w] for idx in LANDMARKS_CLAVE])
        centro = coords.mean(axis=0)
        coords_centradas = coords - centro
        
        p_ojo_izq = np.array([landmarks[33].x * w, landmarks[33].y * h, landmarks[33].z * w])
        p_ojo_der = np.array([landmarks[263].x * w, landmarks[263].y * h, landmarks[263].z * w])
        dist_referencia = np.linalg.norm(p_ojo_izq - p_ojo_der)
        
        if dist_referencia == 0: 
            dist_referencia = 1.0
            
        return (coords_centradas / dist_referencia).flatten()

    def procesar_frame(self, frame):
        h, w, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None, None

        for face_landmarks in results.multi_face_landmarks:
            # Ahora le enviamos el ancho y alto de tu cámara
            features = self.extraer_caracteristicas_clave(face_landmarks.landmark, w, h)
            
            prediccion = self.model.predict([features])[0]

            x_coords = [int(lm.x * w) for lm in face_landmarks.landmark]
            y_coords = [int(lm.y * h) for lm in face_landmarks.landmark]
            
            xmin, xmax = max(0, min(x_coords)), min(w, max(x_coords))
            ymin, ymax = max(0, min(y_coords)), min(h, max(y_coords))

            return prediccion, (xmin, ymin, xmax, ymax)

        return None, None