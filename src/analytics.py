import os
import pandas as pd
import matplotlib.pyplot as plt

def generar_graficas_ux(csv_path="data/registro_patrones_ux.csv"):
    """
    Lee el registro de interacciones CSV y genera gráficas estadísticas
    sobre las emociones detectadas durante la interacción con la IA.
    """
    if not os.path.exists(csv_path):
        print(f"[ERROR] No se encontró el archivo de registro en: {csv_path}")
        print("Realiza algunas interacciones en main.py primero para generar datos.")
        return

    # Leer el archivo CSV
    df = pd.read_csv(csv_path)

    if df.empty or 'emocion' not in df.columns:
        print("[ADVERTENCIA] El archivo CSV está vacío o no contiene la columna 'emocion'.")
        return

    # Contar la frecuencia de cada emoción
    conteo_emociones = df['emocion'].value_counts()

    print("==================================================")
    print("       RESUMEN ESTADÍSTICO DE EMOCIONES UX        ")
    print("==================================================")
    print(conteo_emociones)
    print("--------------------------------------------------")

    # Configuración de estilo para las gráficas
    plt.style.use('ggplot')
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # 1. Gráfica de Barras
    conteo_emociones.plot(
        kind='bar', 
        ax=axes[0], 
        color=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'],
        edgecolor='black'
    )
    axes[0].set_title('Frecuencia de Reacciones Emocionales', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('Emoción Detectada', fontsize=10)
    axes[0].set_ylabel('Cantidad de Interacciones', fontsize=10)
    axes[0].tick_params(axis='x', rotation=45)

    # 2. Gráfica de Pastel (Porcentajes)
    conteo_emociones.plot(
        kind='pie', 
        ax=axes[1], 
        autopct='%1.1f%%', 
        startangle=90,
        colors=['#3498db', '#e74c3c', '#2ecc71', '#f39c12'],
        wedgeprops={'edgecolor': 'black'}
    )
    axes[1].set_title('Distribución Porcentual de Reacciones', fontsize=12, fontweight='bold')
    axes[1].set_ylabel('') # Quitar etiqueta lateral del pie

    # Ajustar diseño y mostrar
    plt.tight_layout()
    
    # Guardar la imagen automáticamente para que la uses en tu reporte
    os.makedirs("data", exist_ok=True)
    ruta_imagen = "data/reporte_emociones_ux.png"
    plt.savefig(ruta_imagen, dpi=300)
    print(f"\n[ÉXITO] Gráfica profesional guardada exitosamente en: {ruta_imagen}")
    
    # Mostrar la ventana con las gráficas
    plt.show()

if __name__ == "__main__":
    generar_graficas_ux()