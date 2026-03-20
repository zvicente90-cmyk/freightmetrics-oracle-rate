# config.py
"""
Configuración centralizada de FreightMetrics MVP
Maneja variables de entorno y validaciones
Soporta tanto desarrollo local como Streamlit Cloud
"""

import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env (solo en desarrollo local)
load_dotenv()

# ============================================
# VARIABLES DE ENTORNO - GOOGLE APIs
# ============================================
# Primero intenta cargar desde Streamlit Secrets (si está en Streamlit Cloud)
# Si no, intenta desde .env o variables de entorno
# Si no, usa fallback (solo para desarrollo local)

try:
    import streamlit as st
    # Si estamos en Streamlit, intentar cargar desde st.secrets
    GOOGLE_MAPS_API_KEY = st.secrets.get("GOOGLE_MAPS_API_KEY", None)
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", None)
except:
    GOOGLE_MAPS_API_KEY = None
    GEMINI_API_KEY = None

# Fallback a ambiente si no está en Streamlit Secrets
if not GOOGLE_MAPS_API_KEY:
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyAsTP4yTb7j7XECoQcsBDMviooAv-v90P8")

if not GEMINI_API_KEY:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDgXuU6LK6ktAmvlyxB84H2DFN_ubuWFcY")

# ============================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))

# ============================================
# BASE DE DATOS
# ============================================
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///freightmetrics.db")

# ============================================
# RUTAS DE ARCHIVOS
# ============================================
DATA_DIR = os.getenv("DATA_DIR", "./data")
MODELS_DIR = os.getenv("MODELS_DIR", "./models")
LOGS_DIR = os.getenv("LOGS_DIR", "./logs")

# Crear directorios si no existen
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ============================================
# FIREBASE (Opcional)
# ============================================
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")

# ============================================
# EMAIL (Opcional)
# ============================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# ============================================
# VALIDACIÓN DE CONFIGURACIÓN
# ============================================
def validate_config():
    """
    Valida que todas las variables requeridas estén configuradas.
    Lanza excepción si falta información crítica.
    """
    required_keys = ["GOOGLE_MAPS_API_KEY", "GEMINI_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        value = os.getenv(key)
        # Si está vacío o es el default fallback, considerar faltante
        if not value or value.startswith("your_"):
            missing_keys.append(key)
    
    if missing_keys:
        error_msg = f"""
⚠️  CONFIGURACIÓN INCOMPLETA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Variables faltantes: {', '.join(missing_keys)}

Por favor configura estas variables en .env:
1. Copia .env.example a .env
2. Llena los valores reales
3. Reinicia la aplicación

Más información: https://github.com/tu-usuario/freightmetrics-mvp/blob/main/SETUP_GITHUB.md
        """
        print(error_msg)
        if not DEBUG:
            raise ValueError(missing_keys)

def print_config_summary():
    """Imprime un resumen de la configuración actual"""
    print("\n" + "="*50)
    print("📋 CONFIGURACIÓN ACTUAL - FreightMetrics")
    print("="*50)
    print(f"✓ Debug: {DEBUG}")
    print(f"✓ Streamlit Port: {STREAMLIT_PORT}")
    print(f"✓ FastAPI Port: {FASTAPI_PORT}")
    print(f"✓ Database: {DATABASE_URL}")
    print(f"✓ Google Maps API: {'✅ Configurado' if GOOGLE_MAPS_API_KEY else '❌ No configurado'}")
    print(f"✓ Gemini API: {'✅ Configurado' if GEMINI_API_KEY else '❌ No configurado'}")
    print("="*50 + "\n")

# Validar configuración al importar el módulo
if __name__ == "__main__":
    try:
        validate_config()
        print_config_summary()
        print("✅ Configuración validada correctamente")
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        sys.exit(1)
