# 📋 GUÍA COMPLETA: Setupeo en GitHub

## Paso 1: Preparar el Repositorio Local

### 1.1 Crear archivo `.env.example`

Este archivo debe incluir todas las variables de entorno necesarias (sin valores sensibles):

```env
# Google APIs
GOOGLE_MAPS_API_KEY=your_google_maps_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Configuración de la app
STREAMLIT_PORT=8501
FASTAPI_PORT=8000
DEBUG=False

# Base de datos (si aplica)
DATABASE_URL=sqlite:///freightmetrics.db

# Firebase (si aplica)
FIREBASE_PROJECT_ID=your_firebase_project_id
FIREBASE_PRIVATE_KEY=your_firebase_private_key
FIREBASE_CLIENT_EMAIL=your_firebase_client_email
```

### 1.2 Actualizar `.gitignore`

Asegúrate que incluya:

```
# Archivos sensibles
.env
.env.local
.env.*.local
config_secret.yaml
*firebase-adminsdk*.json
*-service-account*.json

# Archivos del sistema
.DS_Store
Thumbs.db

# Cache de Python
__pycache__/
*.pyc
*.pyo
*.egg-info/

# Entorno virtual
venv/
.venv/
env/

# Logs
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# Datos temporales
*.tmp
*.cache
```

### 1.3 Crear `.streamlit/secrets.toml` (LOCAL ONLY)

```toml
# Este archivo NO debe commitarse a GitHub
google_maps_api_key = "your_key_here"
gemini_api_key = "your_key_here"
```

Agregar a `.gitignore`:
```
.streamlit/secrets.toml
```

---

## Paso 2: Modificar el Código para Variables de Entorno

### 2.1 Actualizar `requirements.txt`

```
# Core
streamlit>=1.28.0
fastapi>=0.104.0
uvicorn>=0.24.0
python-dotenv>=1.0.0

# Data & Visualization
pandas>=1.5.0
plotly>=5.0.0
numpy>=1.24.0

# APIs & External Services
requests>=2.31.0
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.0.0

# Utilities
PyYAML>=6.0
pydantic>=2.0.0
python-multipart>=0.0.6
streamlit-authenticator>=0.2.0
openpyxl>=3.1.0
```

### 2.2 Crear `config.py` para manejo centralizado de variables

```python
# config.py
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Google APIs
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# App Configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))

# Validar que existan las claves necesarias
def validate_config():
    """Valida que todas las claves de API estén configuradas"""
    required_keys = ["GOOGLE_MAPS_API_KEY", "GEMINI_API_KEY"]
    missing = [key for key in required_keys if not os.getenv(key)]
    
    if missing:
        raise ValueError(f"⚠️ Variables de entorno faltantes: {', '.join(missing)}")

if __name__ == "__main__":
    try:
        validate_config()
        print("✅ Configuración validada correctamente")
    except ValueError as e:
        print(f"❌ Error: {e}")
```

### 2.3 Actualizar `app.py` para usar variables de entorno

**Reemplazar líneas con claves hardcodeadas:**

```python
# ANTES (❌ Inseguro)
GEMINI_API_KEY = "AIzaSyDgXuU6LK6ktAmvlyxB84H2DFN_ubuWFcY"

# DESPUÉS (✅ Seguro)
from config import GEMINI_API_KEY

# Si es None, mostrar error
if not GEMINI_API_KEY:
    st.error("❌ Falta configurar GEMINI_API_KEY en variables de entorno")
    st.stop()
```

**Hacer lo mismo para todas las instancias:**
- Línea 210: `GEMINI_API_KEY`
- Línea 352: `geo_tool = GeoService(api_key=GOOGLE_MAPS_API_KEY)`
- Línea 849: `google_api_key`
- Línea 993: `api_key`

---

## Paso 3: Subir a GitHub

### 3.1 Inicializar repositorio (si no existe)

```bash
cd freightmetrics_mvp
git init
git add .
git commit -m "Initial commit: FreightMetrics MVP"
```

### 3.2 Crear repositorio en GitHub

1. Ir a https://github.com/new
2. Nombre: `freightmetrics-mvp`
3. Descripción: "Sistema de cotización de tarifas de flete spot y análisis predictivo para México"
4. Opciones:
   - ✅ Public (para que otros puedan usarlo)
   - ✅ Agregar README.md (ya lo tienes)
   - ✅ Agregar .gitignore (ya lo tienes)

### 3.3 Conectar repositorio remoto

```bash
git remote add origin https://github.com/tu-usuario/freightmetrics-mvp.git
git branch -M main
git push -u origin main
```

### 3.4 Crear rama `develop` para desarrollo

```bash
git checkout -b develop
git push -u origin develop
```

---

## Paso 4: Configurar Despliegue en Streamlit Cloud

### 4.1 Crear cuenta en Streamlit Cloud

1. Ir a https://streamlit.io/cloud
2. Hacer login con GitHub
3. Autorizar Streamlit para acceder a repositorios

### 4.2 Desplegar la aplicación

1. Click en "New app"
2. Seleccionar: `tu-usuario/freightmetrics-mvp`
3. Branch: `main`
4. Main file path: `app.py`
5. Click "Deploy"

### 4.3 Configurar Secrets en Streamlit Cloud

1. En dashboard de Streamlit Cloud, click en "Advanced settings"
2. Ir a "Secrets" (🔑)
3. Agregar secrets en formato TOML:

```toml
google_maps_api_key = "tu_clave_aqui"
gemini_api_key = "tu_clave_aqui"
```

4. Click "Save" y wait for deployment

---

## Paso 5: Actualizar README.md para GitHub

Agregar esta sección al README:

### 🚀 Despliegue Rápido

#### Localmente

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/freightmetrics-mvp.git
cd freightmetrics-mvp

# 2. Crear ambiente virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env y agregar tus claves de API

# 5. Iniciar servidor backend
python main.py

# 6. En otra terminal, iniciar Streamlit
streamlit run app.py
```

#### En Streamlit Cloud

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://tu-usuario-freightmetrics-mvp.streamlit.app)

1. Fork este repositorio
2. Ir a https://streamlit.io/cloud
3. Click "New app" y selecciona tu fork
4. Configura las variables de entorno en "Secrets"
5. 🎉 ¡Listo!

---

## Paso 6: Pipeline CI/CD (Opcional)

### 6.1 Crear `.github/workflows/tests.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run tests
      run: pytest
```

---

## Paso 7: Checklist Final

Antes de dar por completado:

- [ ] `.env.example` creado y en GitHub
- [ ] `config.py` creado y importado en todos los archivos
- [ ] Todas las claves de API removidas del código
- [ ] `.gitignore` actualizado correctamente
- [ ] `requirements.txt` actualizado
- [ ] README.md incluye instrucciones de despliegue
- [ ] Repositorio pushado a GitHub
- [ ] App deployada en Streamlit Cloud
- [ ] Secrets configurados en Streamlit Cloud
- [ ] Backend (main.py) funciona correctamente
- [ ] Frontend (app.py) se conecta al backend
- [ ] Todas las funcionalidades probadas

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "API key not found"
- Verificar que `.env` existe en raíz del proyecto
- Verificar que las claves están correctas
- En Streamlit Cloud: revisar que Secrets están configurados

### Error: "Connection refused" (Backend)
```bash
# Terminal 1: Backend
python main.py

# Terminal 2: Frontend
streamlit run app.py
```

### Puerto 8000 o 8501 ocupado
```bash
# Cambiar puerto en .env
FASTAPI_PORT=8001
STREAMLIT_PORT=8502
```

---

## 📚 Recursos Adicionales

- [Documentación Streamlit](https://docs.streamlit.io/)
- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Guía GitHub Actions](https://docs.github.com/es/actions)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)

---

**¡Tu aplicación está lista para GitHub! 🚀**
