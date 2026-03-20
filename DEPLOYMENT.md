# 🚀 GUÍA DE DESPLIEGUE - FreightMetrics

## Opción 1: Streamlit Cloud (⭐ Recomendado)

### Ventajas:
- ✅ Despliegue automático desde GitHub
- ✅ No requiere configuración compleja
- ✅ Acceso desde cualquier lugar
- ✅ Subdominio personalizado gratis
- ✅ SSL automático

### Pasos:

1. **Hacer fork del repositorio en GitHub**
   ```
   https://github.com/tu-usuario/freightmetrics-mvp
   ```

2. **Ir a Streamlit Cloud**
   ```
   https://streamlit.io/cloud
   ```

3. **Conectar GitHub**
   - Click en "New app"
   - Seleccionar repo: `freightmetrics-mvp`
   - Branch: `main`
   - Main file: `app.py`
   - Haz click en "Deploy"

4. **Configurar Variables de Entorno**
   - En dashboard de Streamlit Cloud
   - Click en "⋮" (menú) → "Settings"
   - Tab: "Secrets"
   - Agregar claves en formato TOML:

   ```toml
   google_maps_api_key = "tu_clave_aqui"
   gemini_api_key = "tu_clave_aqui"
   ```

5. **URL Pública**
   ```
   https://tu-usuario-freightmetrics-mvp.streamlit.app
   ```

---

## Opción 2: Docker (Local o VPS)

### Crear `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar paquetes Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Crear directorio para datos
RUN mkdir -p /app/data /app/logs

# Variables de entorno
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true

# Exponer puertos
EXPOSE 8501 8000

# Script de inicio
CMD ["sh", "-c", "python main.py & streamlit run app.py"]
```

### Crear `docker-compose.yml`

```yaml
version: '3.8'

services:
  freightmetrics:
    build: .
    ports:
      - "8501:8501"
      - "8000:8000"
    environment:
      - GOOGLE_MAPS_API_KEY=${GOOGLE_MAPS_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - DEBUG=False
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

### Ejecutar:

```bash
# Crear archivo .env con tus claves
cp .env.example .env
# Editar .env y agregar valores

# Desplegar
docker-compose up -d

# Ver logs
docker-compose logs -f freightmetrics
```

---

## Opción 3: Heroku

### Requisitos:
- Cuenta en Heroku (https://www.heroku.com)
- Heroku CLI instalado

### Pasos:

1. **Login en Heroku**
   ```bash
   heroku login
   ```

2. **Crear `Procfile`**
   ```
   web: sh -c 'python main.py & streamlit run app.py --server.port=$PORT'
   ```

3. **Crear `runtime.txt`**
   ```
   python-3.11.0
   ```

4. **Crear aplicación**
   ```bash
   heroku create tu-freightmetrics
   ```

5. **Configurar variables de entorno**
   ```bash
   heroku config:set GOOGLE_MAPS_API_KEY=tu_clave
   heroku config:set GEMINI_API_KEY=tu_clave
   ```

6. **Desplegar**
   ```bash
   git push heroku main
   ```

7. **Ver logs**
   ```bash
   heroku logs --tail
   ```

---

## Opción 4: AWS (EC2)

### Paso a paso:

1. **Lanzar instancia EC2**
   - AMI: Ubuntu Server 22.04 LTS
   - Tipo: t3.micro (Free tier)
   - Security Group: Abrir puertos 8501, 8000

2. **Conectarse por SSH**
   ```bash
   ssh -i tu-key.pem ubuntu@tu-ip-publica
   ```

3. **Instalar dependencias**
   ```bash
   sudo apt update
   sudo apt install -y python3.11 python3.11-venv git
   ```

4. **Clonar repositorio**
   ```bash
   git clone https://github.com/tu-usuario/freightmetrics-mvp.git
   cd freightmetrics-mvp
   ```

5. **Crear ambiente virtual**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   ```

6. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

7. **Configurar variables de entorno**
   ```bash
   nano .env
   # Agregar claves
   ```

8. **Crear servicio systemd**
   ```bash
   sudo nano /etc/systemd/system/freightmetrics.service
   ```

   Contenido:
   ```ini
   [Unit]
   Description=FreightMetrics API & Streamlit
   After=network.target

   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/freightmetrics-mvp
   Environment="PATH=/home/ubuntu/freightmetrics-mvp/venv/bin"
   ExecStart=/bin/bash -c 'python main.py & streamlit run app.py --server.address 0.0.0.0'
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

9. **Iniciar servicio**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable freightmetrics
   sudo systemctl start freightmetrics
   sudo systemctl status freightmetrics
   ```

10. **Acceder a la aplicación**
    ```
    http://tu-ip-publica:8501
    ```

---

## Opción 5: DigitalOcean App Platform

### Ventajas:
- ✅ Despliegue simple desde GitHub
- ✅ SSL automático
- ✅ Escalable
- ✅ Buen soporte

### Pasos:

1. **Ir a DigitalOcean**: https://www.digitalocean.com/
2. **Apps → Create App**
3. **Conectar GitHub repo**
4. **Seleccionar rama: `main`**
5. **Configurar Port**: 8501
6. **Agregar environment variables**:
   - GOOGLE_MAPS_API_KEY
   - GEMINI_API_KEY
7. **Deploy**

---

## Validar Despliegue

Después de desplegar, valida que todo funcione:

```bash
# 1. Verificar que la app está corriendo
curl http://localhost:8501

# 2. Verificar que el backend responde
curl http://localhost:8000/

# 3. Revisar logs
# Depende de tu plataforma (ver arriba)

# 4. Test de predicción
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "route": {
      "distancia_km": 800,
      "tipo_carga": 0,
      "riesgo_pais": 0.3,
      "precio_diesel": 22.0,
      "tiempo_cruce": 6,
      "inflacion_mxn": 5.5,
      "tipo_cambio": 18.0,
      "demanda_mercado": 0.7,
      "capacidad_disponible": 0.6
    }
  }'
```

---

## Troubleshooting

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Puerto en uso
```bash
# Encontrar proceso usando puerto 8501
lsof -i :8501

# Matar proceso
kill -9 PID
```

### Claves de API no funcionan
1. Verificar que están correctamente configuradas
2. Verificar que tienen los permisos correctos en Google Cloud
3. Verificar que no están expiradas

### App lenta
1. Revisar memoria disponible
2. Optimizar queries de base de datos
3. Usar caché de Streamlit

---

## Monitoreo en Producción

### Logging
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Event importante")
logger.error("Error occurred", exc_info=True)
```

### Health Check
Agregar endpoint de salud en `main.py`:
```python
@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
```

### Métricas
Usar Prometheus/Grafana para monitoreo en tiempo real

---

## Actualizaciones

Para actualizar a producción:

```bash
# 1. Hacer cambios en develop
git checkout develop
# ... hacer cambios ...

# 2. Merge a main
git checkout main
git merge develop

# 3. Push a GitHub
git push origin main

# 4. Streamlit Cloud se actualizará automáticamente
# (Ver https://tu-app.streamlit.app)
```

---

**¡Tu aplicación está lista para producción! 🚀**
