# ✅ CHECKLIST PRE-GITHUB

Completa este checklist antes de hacer el primer push a GitHub para asegurar que todo funciona correctamente.

## 🔐 SEGURIDAD

- [ ] **Crear `.env.example`**
  - Contiene estructura de variables pero NO valores sensibles
  - Ubicación: raíz del proyecto

- [ ] **Actualizar `.gitignore`**
  - [ ] Incluye `.env` 
  - [ ] Incluye `*.log`
  - [ ] Incluye `.streamlit/secrets.toml`
  - [ ] Incluye `__pycache__/`
  - [ ] Incluye `.vscode/`
  - [ ] Incluye `*.pyc`

- [ ] **Verificar que NO hay claves en el código**
  ```bash
  # Buscar en todo el repo
  grep -r "AIzaSy" --include="*.py" .
  grep -r "firebase" --include="*.py" .
  # Debe devolver resultados vacíos o solo en archivos de ejemplo
  ```

- [ ] **Crear `config.py`**
  - [ ] Centraliza todas las variables de entorno
  - [ ] Importado en `app.py` y `main.py`
  - [ ] Ubicación: raíz del proyecto

- [ ] **Actualizar scripts para usar variables de entorno**
  - [ ] `app.py` línea 210: usar `from config import GEMINI_API_KEY`
  - [ ] `app.py` línea 352: usar `from config import GOOGLE_MAPS_API_KEY`
  - [ ] `app.py` línea 849: usar config
  - [ ] `app.py` línea 993: usar config
  - [ ] `main.py`: usar config (si aplica)

---

## 📦 DEPENDENCIAS

- [ ] **`requirements.txt` actualizado**
  - [ ] Contiene todas las librerías necesarias
  - [ ] Versiones específicas (no wild cards)
  - [ ] Incluye `python-dotenv`
  - [ ] Incluye `streamlit>=1.28.0`
  - [ ] Incluye `fastapi>=0.104.0`

- [ ] **Test local de instalación**
  ```bash
  python -m venv test_env
  source test_env/bin/activate
  pip install -r requirements.txt
  # Sin errores = ✅
  ```

---

## 📝 DOCUMENTACIÓN

- [ ] **README.md**
  - [ ] Descripción clara del proyecto
  - [ ] Características principales
  - [ ] Instrucciones de instalación local
  - [ ] Instrucciones de despliegue
  - [ ] Sección de variables de entorno
  - [ ] Troubleshooting

- [ ] **SETUP_GITHUB.md** 
  - [ ] Creado y en raíz del proyecto
  - [ ] Incluye instrucciones paso a paso

- [ ] **DEPLOYMENT.md**
  - [ ] Creado y en raíz del proyecto
  - [ ] Opciones para Streamlit Cloud, Docker, Heroku, AWS

- [ ] **Comentarios en código**
  - [ ] Funciones complejas tienen docstrings
  - [ ] Secciones críticas tienen comentarios
  - [ ] No hay código muerto comentado

---

## 🧪 PRUEBAS

- [ ] **Backend funciona localmente**
  ```bash
  python main.py
  # Debe iniciar en http://localhost:8000
  # GET / debe devolver status 200
  ```

- [ ] **Frontend funciona localmente**
  ```bash
  streamlit run app.py
  # Debe abrir en http://localhost:8501
  ```

- [ ] **Se conectan entre sí**
  - [ ] Frontend puede llamar al backend
  - [ ] No hay errores de CORS
  - [ ] Las predicciones funcionan

- [ ] **APIs externas funcionan**
  - [ ] Google Maps API responde
  - [ ] Gemini API responde
  - [ ] Datos de diesel se cargan correctamente

- [ ] **Autenticación y rutas de usuario**
  - [ ] Login funciona
  - [ ] Logout funciona
  - [ ] Planes de suscripción se muestran
  - [ ] Acceso denegado para usuarios no autenticados

---

## 📊 DATOS

- [ ] **Archivos JSON necesarios existen**
  - [ ] `dat_rates_us.json`
  - [ ] `matriz_comparativa_mx.json`
  - [ ] `freightmetrics_historical.json`
  - [ ] `index_spot_tarifas.json`

- [ ] **Base de datos (si aplica)**
  - [ ] No incluye datos sensibles
  - [ ] .gitignore excluye archivos de BD

---

## 🌐 GIT & GITHUB

- [ ] **Repositorio Git inicializado**
  ```bash
  cd freightmetrics_mvp
  git status
  # Debe mostrar estado del repo
  ```

- [ ] **`.gitignore` funciona correctamente**
  ```bash
  git add . --dry-run
  # NO debe incluir .env, .pyc, __pycache__, etc.
  ```

- [ ] **Primer commit hecho**
  ```bash
  git add .
  git commit -m "Initial commit: FreightMetrics MVP"
  ```

- [ ] **Repositorio creado en GitHub**
  - [ ] https://github.com/nuevo-repo (sin raíz)
  - [ ] Descripción clara
  - [ ] Público (para que otros lo vean)

- [ ] **Remoto agregado**
  ```bash
  git remote -v
  # Debe mostrar origin apuntando a GitHub
  ```

- [ ] **Primer push completado**
  ```bash
  git push -u origin main
  # Sin errores = ✅
  ```

---

## 🚀 DESPLIEGUE

- [ ] **Habilitar Streamlit Cloud**
  - [ ] Cuenta en https://streamlit.io/cloud creada
  - [ ] Autorización GitHub completada
  - [ ] Aplicación deployada

- [ ] **Secrets en Streamlit Cloud configurados**
  - [ ] En "Advanced settings" → "Secrets"
  - [ ] GOOGLE_MAPS_API_KEY agregada
  - [ ] GEMINI_API_KEY agregada

- [ ] **URL pública funciona**
  ```
  https://tu-usuario-freightmetrics-mvp.streamlit.app
  ```
  - [ ] Carga correctamente
  - [ ] Puede navegar por las páginas
  - [ ] Cotizador genera predicciones

- [ ] **Backend en Streamlit Cloud funciona** (si aplica)
  - [ ] API responde en contexto cloud
  - [ ] Conexión a servicios externos funciona

---

## 📋 DOCUMENTACIÓN FINAL

- [ ] **Wiki de GitHub**
  - [ ] Crear wiki con guías adicionales
  - [ ] Documentar API endpoints
  - [ ] Incluir ejemplos de uso

- [ ] **Issues template**
  - [ ] Crear `.github/ISSUE_TEMPLATE/bug_report.md`
  - [ ] Crear `.github/ISSUE_TEMPLATE/feature_request.md`

- [ ] **Pull Request template**
  - [ ] Crear `.github/pull_request_template.md`

---

## 🔍 VALIDACIÓN FINAL

- [ ] **Revisar en GitHub que se vea bien**
  - [ ] README se renderiza correctamente
  - [ ] Estructura de carpetas está clara
  - [ ] No hay archivos sensibles visibles

- [ ] **Probar con usuario nuevo**
  - [ ] Clonar repo en otra carpeta
  - [ ] Seguir instrucciones del README
  - [ ] Todo funciona sin problemas

- [ ] **Compartir con el equipo**
  - [ ] GitHub URL compartida
  - [ ] Instrucciones de setup compartidas
  - [ ] Feedback recibido

---

## 🎉 ¡LISTO!

Si completaste todos los puntos:

```
 ✅ Seguridad configurada
 ✅ Código documentado
 ✅ Pruebas pasadas
 ✅ Deployado en producción
 ✅ Listo para colaboradores
```

**¡Tu proyecto está en GitHub y funcionando correctamente! 🚀**

---

## 📞 Soporte

Si algo no funciona:

1. Revisar [SETUP_GITHUB.md](SETUP_GITHUB.md#troubleshooting)
2. Revisar [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting)
3. Crear un issue en GitHub describiendo el problema
4. Incluir:
   - Pasos para reproducir
   - Error exacto
   - Sistema operativo
   - Versión de Python

---

**Última actualización: 20/03/2026**
