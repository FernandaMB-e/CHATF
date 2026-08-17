import os
import pandas as pd

def analizar_patrones_ux(csv_path="registro_patrones.csv"):
    """
    Lee el archivo de registros y genera un informe estadístico 
    sobre las emociones provocadas por los fallos de la IA.
    """
    if not os.path.exists(csv_path):
        print(f"[AVISO] No se encontró el archivo de registros en: {csv_path}")
        print("Ejecuta al menos una prueba en el sistema principal para generar datos.")
        return

    # Cargar los datos con pandas
    df = pd.read_csv(csv_path)
    
    if df.empty:
        print("[AVISO] El archivo de registro está vacío.")
        return

    print("==================================================")
    print("          INFORME DE PATRONES DE UX               ")
    print("==================================================")
    print(f"Total de interacciones analizadas: {len(df)}\n")

    # 1. Conteo general de reacciones emocionales
    print("--- 1. Distribución General de Emociones ---")
    conteo_emociones = df['Emocion_Dominante'].value_counts()
    for emocion, cantidad in conteo_emociones.items():
        porcentaje = (cantidad / len(df)) * 100
        print(f"  * {emocion.upper()}: {cantidad} registros ({porcentaje:.1f}%)")
    print("\n")

    # 2. Relación entre categoría de fallo y emoción generada
    print("--- 2. Impacto Emocional por Categoría de Fallo ---")
    if 'Categoria' in df.columns and 'Emocion_Dominante' in df.columns:
        cruce = pd.crosstab(df['Categoria'], df['Emocion_Dominante'])
        print(cruce)
        print("\n")

    # 3. Detalle por caso de prueba específico
    print("--- 3. Desglose por Caso Específico ---")
    for caso_id, grupo in df.groupby('ID_Caso'):
        pregunta = grupo['Pregunta'].iloc[0]
        categoria = grupo['Categoria'].iloc[0]
        
        # Obtener la emoción más frecuente para este caso
        modo_emocion = grupo['Emocion_Dominante'].mode()
        emocion_comun = modo_emocion[0].upper() if not modo_emocion.empty else "N/A"
        
        print(f"Caso #{caso_id} [{categoria}]")
        print(f"  -> Pregunta: \"{pregunta}\"")
        print(f"  -> Reacción predominante: {emocion_comun} (Pruebas realizadas: {len(grupo)})")
        print("-" * 50)

    print("==================================================")
    print("[SISTEMA] Análisis de patrones completado con éxito.")

if __name__ == "__main__":
    analizar_patrones_ux()