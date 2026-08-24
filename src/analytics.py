import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def generar_graficas_comparativas_ux(csv_path="data/registro_patrones_ux.csv"):
    """
    Lee el registro del ciclo de computación afectiva y genera gráficas 
    comparando la emoción Fase 1 (Choque) vs Fase 2 (Compensación).
    """
    if not os.path.exists(csv_path):
        print(f"[ERROR] No se encontró el archivo de registro en: {csv_path}")
        return

    df = pd.read_csv(csv_path)

    if df.empty or 'Emocion_Fase1' not in df.columns or 'Emocion_Fase2' not in df.columns:
        print("[ADVERTENCIA] El archivo CSV está vacío o no tiene las columnas de ambas fases.")
        return

    # Contar las frecuencias de ambas fases
    fase1_counts = df['Emocion_Fase1'].value_counts()
    fase2_counts = df['Emocion_Fase2'].value_counts()

    # Unificar todas las emociones detectadas para alinear las barras
    todas_emociones = list(set(fase1_counts.keys()).union(set(fase2_counts.keys())))
    
    valores_fase1 = [fase1_counts.get(emocion, 0) for emocion in todas_emociones]
    valores_fase2 = [fase2_counts.get(emocion, 0) for emocion in todas_emociones]

    print("==================================================")
    print("    COMPARATIVA DE EMOCIONES (ANTES Y DESPUÉS)    ")
    print("==================================================")
    for emocion, v1, v2 in zip(todas_emociones, valores_fase1, valores_fase2):
        print(f"{emocion.upper():<15} | Fase 1: {v1}  ->  Fase 2: {v2}")
    print("--------------------------------------------------")

    # Configuración de la gráfica comparativa
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(10, 6))

    x = np.arange(len(todas_emociones))
    width = 0.35

    barras1 = ax.bar(x - width/2, valores_fase1, width, label='Fase 1 (Respuesta Incoherente)', color='#e74c3c', edgecolor='black')
    barras2 = ax.bar(x + width/2, valores_fase2, width, label='Fase 2 (Respuesta Compensatoria)', color='#2ecc71', edgecolor='black')

    ax.set_ylabel('Cantidad de Interacciones', fontsize=12)
    ax.set_title('Evolución de la Experiencia de Usuario', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([e.capitalize() for e in todas_emociones], fontsize=11)
    ax.legend()

    plt.tight_layout()
    
    # Guardar imagen para documentación
    os.makedirs("data", exist_ok=True)
    ruta_imagen = "data/comparativa_fases_ux.png"
    plt.savefig(ruta_imagen, dpi=300)
    print(f"\n[ÉXITO] Gráfica comparativa guardada en: {ruta_imagen}")
    
    plt.show()

if __name__ == "__main__":
    generar_graficas_comparativas_ux()