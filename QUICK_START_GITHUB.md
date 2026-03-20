# 🚀 GUÍA RÁPIDA - FreightMetrics a GitHub en 10 minutos

> Versión simplificada para subir tu proyecto a GitHub correctamente

---

## ⚡ Paso 1: Preparar Proyecto Localmente (3 min)

```bash
# 1. Ir al directorio del proyecto
cd freightmetrics_mvp

# 2. Crear archivo .env (NUNCA versionarlo)
cp .env.example .env
# Editar .env y agregar tus claves:
# - GOOGLE_MAPS_API_KEY=tu_clave
# - GEMINI_API_KEY=tu_clave
nano .env

# 3. Verificar que .gitignore está bien
cat .gitignore | grep -E "\.env|\.pyc|__pycache__|\.vscode"
# Debe mostrar líneas (si no, verificar que el archivo tenga contenido)

# 4. Probar que funciona localmente
python main.py &
streamlit run app.py
# Ambas deben iniciarse sin errores
# Matar procesos: Ctrl+C
pkill -f streamlit
pkill -f main.py
```

---

## 📤 Paso 2: Inicializar Git (2 min)

```bash
# 1. Verificar si Git ya está inicializado
git status

# Si NO está inicializado (error):
git init

# 2. Agregar todos los archivos (excepto .env - lo cubre .gitignore)
git add .

# 3. Verificar que NO está agregando .env
git status | grep ".env"
# Debe estar VACÍO (no debe mencionar .env)

# 4. Hacer commit inicial
git commit -m "🚀 Initial commit: FreightMetrics MVP - Cotizador de tarifas spot"

# 5. Cambiar rama a 'main' si es necesario
git branch -M main
```

---

## 🌐 Paso 3: Crear Repositorio en GitHub (2 min)

1. Ir a: https://github.com/new

2. Llenar formulario:
   - **Repository name**: `freightmetrics-mvp`
   - **Description**: `Sistema de cotización de tarifas de flete spot y análisis predictivo para México`
   - **Public** ✅ (para que otros lo vean)
   - **NO marcar** "Initialize with README" (ya lo tienes)

3. Click en **"Create repository"**

---

## 🔗 Paso 4: Conectar y Push (1 min)

```bash
# 1. Agregar remoto (copiar desde GitHub después de crear repo)
git remote add origin https://github.com/TU-USUARIO/freightmetrics-mvp.git

# 2. Verificar remoto
git remote -v

# 3. Hacer push
git push -u origin main

# Si pide autenticación:
# - Crear token en GitHub: https://github.com/settings/tokens
# - O usar "git credential manager" (más fácil)
```

---

## 🎯 Paso 5: Desplegar en Streamlit Cloud (2 min)

### Opción A: Automático desde GitHub (⭐ Recomendado)

1. Ir a: https://streamlit.io/cloud
2. Login con GitHub
3. Click en **"New app"**
4. Seleccionar:
   - Repository: `tu-usuario/freightmetrics-mvp`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **"Deploy"**

### Agregue Secrets en Streamlit Cloud:

1. En dashboard, click en **⋮** (menú) → **"Settings"**
2. Tab: **"Secrets"**
3. Copiar y pegar:

```toml
google_maps_api_key = "cola_real_aqui"
gemini_api_key = "clave_real_aqui"
```

4. Save → Esperar 2-3 minutos para que redeploy

**Tu app estará en:**
```
https://tu-usuario-freightmetrics-mvp.streamlit.app
```

---

## ✅ Verificar que Todo Funciona

```bash
# 1. Verificar que está en GitHub
open https://github.com/tu-usuario/freightmetrics-mvp

# 2. Verificar que Streamlit Cloud nota los cambios
open https://share.streamlit.io/tu-usuario/freightmetrics-mvp/main/app.py

# 3. Probar las funcionalidades:
# - Ingresar origen y destino
# - Hacer una predicción
# - Ver gráficos
# - Cambiar parámetros
```

---

## 📱 Compartir con el Mundo

Tu proyecto está listo en:
```
GitHub: https://github.com/tu-usuario/freightmetrics-mvp
Demo: https://tu-usuario-freightmetrics-mvp.streamlit.app
```

Puedes compartir estas URLs en:
- Twitter/X
- LinkedIn
- Portfolio
- Email a clientes
- Portafolio de GitHub

---

## 🔄 Actualizar Código (Futuro)

Si necesitas hacer cambios:

```bash
# 1. Hacer cambios en el código
nano app.py  # editar

# 2. Commit
git add .
git commit -m "✨ Agregué nueva funcionalidad"

# 3. Push
git push

# 4. Streamlit Cloud se actualiza automáticamente en 1-2 minutos
# (Ver https://tu-usuario-freightmetrics-mvp.streamlit.app)
```

---

## 🆘 Si Algo No Funciona

### Error: ".env no encontrado"
```bash
# Verificar que existe
ls -la .env

# Si no existe, crear desde .env.example
cp .env.example .env
nano .env  # editar claves
```

### Error: "API key not found" en Streamlit Cloud
1. Ir a Settings → Secrets
2. Verificar que las claves están ahí
3. Reiniciar con "Reboot app" arriba a la derecha

### Error: Git "origin already exists"
```bash
# Cambiar remoto
git remote set-url origin https://github.com/tu-usuario/freightmetrics-mvp.git
git push -u origin main
```

### Backend no conecta en Streamlit Cloud
Streamlit Cloud ejecuta solo aplicaciones Streamlit. Para ejecutar FastAPI También necesitas:
- Docker + Heroku
- O solo mantener Streamlit

---

## 📊 Próximos Pasos (Opcional)

- [ ] Crear badges en README (Build status, etc)
- [ ] Configurar GitHub Actions para pruebas automáticas
- [ ] Agregue GitHub Pages para documentación
- [ ] Habilitar Discussions para comunidad
- [ ] Crear Issues template
- [ ] Crear Pull Request template

---

## 🎉 ¡Listo!

Tu aplicación FreightMetrics ahora está:
- ✅ En GitHub
- ✅ Deployada en Streamlit Cloud
- ✅ Accesible públicamente
- ✅ Actualizable automáticamente

**Tiempo total: ~10 minutos** ⏱️

---

**Necesitas ayuda?** Ver:
- [SETUP_GITHUB.md](SETUP_GITHUB.md) - Guía completa
- [DEPLOYMENT.md](DEPLOYMENT.md) - Otras opciones de despliegue
- [CHECKLIST_GITHUB.md](CHECKLIST_GITHUB.md) - Lista de verificación
