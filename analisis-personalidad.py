import json
import os
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Cargar configuración de seguridad (.env)
load_dotenv()

class PersonalityAnalyzer:
    """
    Servicio de análisis psicológico mediante IA de última generación.
    Implementa el modelo Big Five para perfilar usuarios de redes sociales.
    """
    def __init__(self):
        # Recuperar la API KEY del archivo .env
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ Error: GEMINI_API_KEY no encontrada en el .env")
        
        # Configurar el SDK de Google
        genai.configure(api_key=self.api_key)
        
        # 🚀 Usando la serie 2.5 para máxima precisión y velocidad
        # Si tu SDK es muy reciente, usa 'gemini-2.5-flash'. 
        # Si falla, cámbialo a 'models/gemini-1.5-flash' como respaldo.
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(self.model_name)

    def analizar_perfil_json(self, ruta_archivo):
        print(f"--- Iniciando Pipeline de Análisis NLP ---")
        print(f"[→] Cargando datos desde: {ruta_archivo}")
        
        try:
            # Lectura del JSON extraído por el scraper
            with open(ruta_archivo, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            # Definición del Prompt de Ingeniería (Prompt Engineering)
            prompt = f"""
            Eres un sistema experto en psicología conductual y análisis de Big Data.
            Analiza el siguiente dataset de Instagram y construye un perfil psicológico 
            basado en el modelo Big Five (OCEAN).

            DATASET: {json.dumps(raw_data)}

            ESTRUCTURA DEL REPORTE:
            1. Puntuación Cuantitativa (0-100%): 
               - Apertura, Responsabilidad, Extraversión, Amabilidad, Neuroticismo.
            2. Análisis Cualitativo: Justifica cada rasgo analizando el tono de los 
               comentarios y el tipo de marcas publicitarias (ej. FashionNova, L'Oréal).
            3. Conclusión: Resume el comportamiento digital del usuario.
            """

            print(f"[🚀] Consultando modelo {self.model_name}...")
            response = self.model.generate_content(prompt)
            return response.text

        except FileNotFoundError:
            return "❌ Error: No se encontró el archivo JSON. Verifica la ruta."
        except Exception as e:
            return f"❌ Excepción en el consumo de la API: {e}"

if __name__ == "__main__":
    # Ejecución del módulo
    try:
        analyzer = PersonalityAnalyzer()
        reporte_final = analyzer.analizar_perfil_json("amarantavp_limpio.json")
        
        print("\n" + "="*60)
        print("📊 INFORME PSICOLÓGICO GENERADO (MODELO GEMINI 2.5)")
        print("="*60)
        print(reporte_final)
        
        # Persistencia del resultado en disco
        with open("reporte_personalidad_final.txt", "w", encoding="utf-8") as f:
            f.write(reporte_final)
        print("\n[✅] Informe guardado exitosamente como 'reporte_personalidad_final.txt'")

    except Exception as e:
        print(f"Fallo en la ejecución: {e}")